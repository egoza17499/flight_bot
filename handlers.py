import asyncio
import os
import logging
from datetime import datetime, timedelta
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import (
    add_user, update_user_field, set_registered, get_user, get_all_users,
    search_info, add_info, delete_info, get_all_info,
    is_admin, add_admin, remove_admin, get_all_admins
)
from states import Registration, EditProfile, SearchInfo, AdminStates
from keyboards import (
    get_main_menu, get_edit_menu, get_admin_menu, get_admin_manage_menu,
    FIELD_MAP, FIELD_NAMES
)
from utils import parse_date, generate_profile_text, check_flight_ban
from config import ADMIN_ID, BOT_VERSION
from airports_data import AIRPORTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

# ========== ХРАНЕНИЕ ПОСЛЕДНИХ СООБЩЕНИЙ ==========
last_bot_messages = {}
last_sent_results = {}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def delete_message_safe(message: types.Message):
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"Не удалось удалить сообщение: {e}")

async def cleanup_last_bot_message(message: types.Message):
    chat_id = message.chat.id
    if chat_id in last_bot_messages:
        try:
            await message.bot.delete_message(chat_id, last_bot_messages[chat_id])
        except Exception as e:
            logger.debug(f"Не удалось удалить старое сообщение: {e}")
        finally:
            if chat_id in last_bot_messages:
                del last_bot_messages[chat_id]

async def send_and_save(message: types.Message, text: str, **kwargs):
    sent_message = await message.answer(text, **kwargs)
    last_bot_messages[message.chat.id] = sent_message.message_id
    return sent_message

def is_duplicate_result(chat_id: int, query: str, result_text: str) -> bool:
    if chat_id in last_sent_results:
        last_query, last_result = last_sent_results[chat_id]
        if query.lower() == last_query.lower() and result_text == last_result:
            return True
    return False

def save_search_result(chat_id: int, query: str, result_text: str):
    last_sent_results[chat_id] = (query, result_text)

def is_admin_check(user_id):
    return user_id == ADMIN_ID

def get_persistent_menu(is_admin=False):
    """Постоянное закреплённое меню внизу"""
    kb = [
        [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="📚 Полезная информация")],
    ]
    if is_admin:
        kb.append([KeyboardButton(text="🛡 Функции админа")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, persistent=True)

def check_deadline_status(date_str, field_name=""):
    """
    Проверяет статус срока
    Returns: (color, message)
    - red: просрочено
    - yellow: меньше 30 дней
    - green: всё хорошо
    """
    if not date_str or date_str.lower() in ['нет', 'не пройдено', 'б/к', '']:
        return "red", f"{field_name}: не пройдено"
    
    try:
        # Пробуем распарсить дату в формате ДД.ММ.ГГГГ
        deadline = datetime.strptime(date_str, "%d.%m.%Y")
        now = datetime.now()
        delta = deadline - now
        
        if delta.days < 0:
            return "red", f"{field_name}: просрочено ({abs(delta.days)} дн. назад)"
        elif delta.days < 30:
            return "yellow", f"{field_name}: осталось {delta.days} дн."
        else:
            return "green", "OK"
    except:
        return "green", "OK"

def get_user_status_with_colors(user):
    """Формирует текст статуса пользователя с цветовой индикацией"""
    bans = check_flight_ban(user)
    
    if bans:
        # Есть нарушения - красным
        status_text = "🔴 <b>НАРУШЕНИЯ:</b>\n"
        for ban in bans:
            status_text += f"  • {ban}\n"
        return status_text
    else:
        # Проверяем все сроки
        checks = [
            (user.get('vlk_date'), "ВЛК"),
            (user.get('umo_date'), "УМО"),
            (user.get('kbp_4_md_m'), "КБП-4 МД-М"),
            (user.get('kbp_7_md_m'), "КБП-7 МД-М"),
            (user.get('kbp_4_md_90a'), "КБП-4 МД-90А"),
            (user.get('kbp_7_md_90a'), "КБП-7 МД-90А"),
        ]
        
        status_parts = []
        has_warning = False
        
        for date_val, name in checks:
            if date_val and date_val.lower() not in ['нет', 'не пройдено', 'б/к', '']:
                color, msg = check_deadline_status(date_val, name)
                if color == "red":
                    status_parts.append(f"🔴 {msg}")
                    has_warning = True
                elif color == "yellow":
                    status_parts.append(f"🟡 {msg}")
                    has_warning = True
        
        if status_parts:
            return "⚠️ <b>ВНИМАНИЕ:</b>\n" + "\n".join(status_parts)
        else:
            return "🟢 <b>Всё в порядке</b>"

def extract_airport_info(query: str, result_text: str) -> str:
    info = ""
    query_lower = query.lower()
    
    airports_map = {
        "стригино": ("Нижний Новгород", "Аэропорт Стригино"),
        "чкаловский": ("Москва", "Аэродром Чкаловский"),
        "пулково": ("Санкт-Петербург", "Аэропорт Пулково"),
        "внуково": ("Москва", "Аэропорт Внуково"),
        "кольцово": ("Екатеринбург", "Аэропорт Кольцово"),
    }
    
    for key, (city, airport) in airports_map.items():
        if key in query_lower:
            info += f"🏙 <b>Город:</b> {city}\n"
            info += f"✈️ <b>Аэродром:</b> {airport}"
            break
    
    return info

# ========== СТАРТ И РЕГИСТРАЦИЯ ==========

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await add_user(message.from_user.id, message.from_user.username)
    user = await get_user(message.from_user.id)
    admin = is_admin_check(message.from_user.id)
    
    if user and user.get('registered'):
        await send_and_save(
            message,
            "Добро пожаловать обратно! Выберите действие:",
            reply_markup=get_persistent_menu(is_admin=admin)
        )
    else:
        await send_and_save(
            message,
            "👋 Приветствую! Для доступа к функциям необходимо пройти регистрацию.\n\n"
            "Начнем? (Напишите /start еще раз или просто начните вводить данные)",
            reply_markup=get_persistent_menu(is_admin=admin)
        )
        await state.set_state(Registration.fio)
        await send_and_save(message, "1️⃣ Введите вашу Фамилию Имя Отчество:")

@router.message(Registration.fio)
async def reg_fio(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await update_user_field(message.from_user.id, 'fio', message.text)
    await state.set_state(Registration.rank)
    await send_and_save(message, "2️⃣ Введите воинское звание:")

@router.message(Registration.rank)
async def reg_rank(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await update_user_field(message.from_user.id, 'rank', message.text)
    await state.set_state(Registration.qual_rank)
    await send_and_save(message, "3️⃣ Введите квалификационный разряд:")

@router.message(Registration.qual_rank)
async def reg_qual(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await update_user_field(message.from_user.id, 'qual_rank', message.text)
    await state.set_state(Registration.vacation)
    await send_and_save(message, "4️⃣ Введите даты крайнего отпуска (формат: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ):")

@router.message(Registration.vacation)
async def reg_vacation(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    try:
        if '-' not in message.text:
            await send_and_save(message, "❌ Неверный формат! Используйте: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ")
            return
        parts = message.text.split('-')
        if len(parts) != 2:
            await send_and_save(message, "❌ Ошибка формата! Введите две даты через дефис")
            return
        await update_user_field(message.from_user.id, 'vacation_start', parts[0].strip())
        await update_user_field(message.from_user.id, 'vacation_end', parts[1].strip())
        await state.set_state(Registration.vlk)
        await send_and_save(message, "5️⃣ Введите дату прохождения ВЛК (ДД.ММ.ГГГГ):")
    except Exception as e:
        await send_and_save(message, f"❌ Ошибка: {e}")

@router.message(Registration.vlk)
async def reg_vlk(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await update_user_field(message.from_user.id, 'vlk_date', message.text)
    await state.set_state(Registration.umo)
    await send_and_save(message, "6️⃣ Введите дату прохождения УМО (ДД.ММ.ГГГГ). Если не было - напишите 'нет':")

@router.message(Registration.umo)
async def reg_umo(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    val = message.text if message.text.lower() != 'нет' else None
    await update_user_field(message.from_user.id, 'umo_date', val)
    await state.set_state(Registration.kbp_4_md_m)
    await send_and_save(message, "7️⃣ КБП-4 Ил-76 МД-М (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_4_md_m)
async def reg_kbp4m(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await update_user_field(message.from_user.id, 'kbp_4_md_m', message.text)
    await state.set_state(Registration.kbp_7_md_m)
    await send_and_save(message, "8️⃣ КБП-7 Ил-76 МД-М (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_7_md_m)
async def reg_kbp7m(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await update_user_field(message.from_user.id, 'kbp_7_md_m', message.text)
    await state.set_state(Registration.kbp_4_md_90a)
    await send_and_save(message, "9️⃣ КБП-4 Ил-76 МД-90А (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_4_md_90a)
async def reg_kbp4_90(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await update_user_field(message.from_user.id, 'kbp_4_md_90a', message.text)
    await state.set_state(Registration.kbp_7_md_90a)
    await send_and_save(message, "🔟 КБП-7 Ил-76 МД-90А (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_7_md_90a)
async def reg_kbp7_90(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await update_user_field(message.from_user.id, 'kbp_7_md_90a', message.text)
    await state.set_state(Registration.jumps)
    await send_and_save(message, "1️⃣1️⃣ Дата выполнения прыжков с парашютом (ДД.ММ.ГГГГ):")

@router.message(Registration.jumps)
async def reg_finish(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await update_user_field(message.from_user.id, 'jumps_date', message.text)
    await set_registered(message.from_user.id)
    await state.clear()
    user = await get_user(message.from_user.id)
    admin = is_admin_check(message.from_user.id)
    
    bans = check_flight_ban(user)
    if bans:
        ban_text = "\n".join(bans)
        await send_and_save(
            message,
            f"⚠️ ВНИМАНИЕ!\n{ban_text}",
            reply_markup=get_persistent_menu(is_admin=admin)
        )
    else:
        await send_and_save(
            message,
            "✅ Регистрация успешно завершена!",
            reply_markup=get_persistent_menu(is_admin=admin)
        )

# ========== ГЛАВНОЕ МЕНЮ ==========

@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: types.Message):
    await cleanup_last_bot_message(message)
    user = await get_user(message.from_user.id)
    if not user or not user.get('registered'):
        await send_and_save(message, "Сначала пройдите регистрацию (/start)")
        return
    
    text = generate_profile_text(user)
    bans = check_flight_ban(user)
    if bans:
        text += "\n\n🚫 <b>ПОЛЕТЫ ЗАПРЕЩЕНЫ!</b>\n" + "\n".join(bans)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_start")]])
    await send_and_save(message, text, reply_markup=kb)

@router.message(F.text == "📚 Полезная информация")
async def start_search(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await state.set_state(SearchInfo.waiting_query)
    quick_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Чкаловский"), KeyboardButton(text="🔍 Стригино")],
            [KeyboardButton(text="🔍 Москва"), KeyboardButton(text="🔍 Санкт-Петербург")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    await send_and_save(
        message, 
        "🔍 Напишите город или аэродром, информация по которому вас интересует:",
        reply_markup=quick_kb
    )

@router.message(SearchInfo.waiting_query)
async def process_search(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    query = message.text.strip()
    
    if query.lower() == "отмена" or query == "❌ Отмена":
        await state.clear()
        admin = is_admin_check(message.from_user.id)
        await send_and_save(message, "❌ Поиск отменен", reply_markup=get_persistent_menu(is_admin=admin))
        return
    
    results = await search_info(query)
    
    if results:
        for result_text in results:
            if is_duplicate_result(message.chat.id, query, result_text):
                logger.info(f"⏭ Пропущен дубликат для '{query}'")
                continue
            
            save_search_result(message.chat.id, query, result_text)
            
            header = f"🔍 <b>Вот что смог найти по запросу: {query}</b>\n\n"
            airport_info = extract_airport_info(query, result_text)
            if airport_info:
                header += airport_info + "\n\n"
            header += "<b>Полезные номера:</b>\n"
            
            full_text = header + result_text
            await message.answer(full_text)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать другой поиск", callback_data="new_search")]
        ])
        await send_and_save(message, "❌ Информация не найдена, извините.", reply_markup=kb)
    
    await state.clear()

@router.callback_query(F.data == "new_search")
async def new_search_callback(callback: types.CallbackQuery):
    await callback.message.answer(
        "🔍 Введите новый запрос:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Чкаловский"), KeyboardButton(text="🔍 Стригино")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    )
    await callback.answer()

@router.message(F.text == "🛡 Функции админа")
async def admin_menu_button(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        await send_and_save(message, "❌ Доступ запрещен.")
        return
    await send_and_save(
        message,
        "🛡 <b>Панель администратора</b>\n\nВыберите действие:",
        reply_markup=get_admin_menu()
    )

# ========== РЕДАКТИРОВАНИЕ ==========

@router.callback_query(F.data == "edit_start")
async def start_edit(callback: types.CallbackQuery):
    await callback.message.edit_text("✏️ Выберите параметр:", reply_markup=get_edit_menu())
    await callback.answer()

@router.callback_query(F.data.startswith("edit_"))
async def choose_field_edit(callback: types.CallbackQuery, state: FSMContext):
    field_key = callback.data.replace("edit_", "")
    field_name = FIELD_NAMES.get(field_key, field_key)
    await state.set_state(EditProfile.entering_value)
    await state.update_data(edit_field=field_key)
    kb = [[InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_profile")]]
    await callback.message.edit_text(
        f"✏️ Введите значение для: <b>{field_name}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user = await get_user(callback.from_user.id)
    if user and user.get('registered'):
        text = generate_profile_text(user)
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_start")]])
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()

@router.message(EditProfile.entering_value)
async def save_edit(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    data = await state.get_data()
    field_key = data.get('edit_field')
    if not field_key:
        await send_and_save(message, "❌ Ошибка")
        await state.clear()
        return
    if field_key == "vacation":
        parts = message.text.split('-')
        if len(parts) == 2:
            await update_user_field(message.from_user.id, 'vacation_start', parts[0].strip())
            await update_user_field(message.from_user.id, 'vacation_end', parts[1].strip())
            await send_and_save(message, "✅ Обновлено!")
    else:
        db_field = FIELD_MAP.get(field_key)
        if db_field:
            await update_user_field(message.from_user.id, db_field, message.text)
            await send_and_save(message, "✅ Обновлено!")
    await state.clear()
    await show_profile(message)

# ========== АДМИН ПАНЕЛЬ ==========

@router.callback_query(F.data == "admin_list")
async def admin_list_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    
    users = await get_all_users()
    if not users:
        await callback.message.answer("📋 Список пуст.")
        await callback.answer()
        return
    
    output = "📋 <b>Список личного состава:</b>\n\n"
    
    for i, u in enumerate(users, 1):
        # Добавляем кнопку с callback_data для просмотра полной анкеты
        user_id = u['user_id']
        fio = u['fio']
        rank = u['rank']
        
        # Получаем статус с цветовой индикацией
        status_text = get_user_status_with_colors(u)
        
        output += f"{i}. 👤 {fio}\n"
        output += f"   Звание: {rank}\n"
        if u.get('qual_rank'):
            output += f"   Квалификация: {u['qual_rank']}\n"
        output += f"   {status_text}\n"
        output += f"   /user{user_id}\n\n"
    
    # Разбиваем на сообщения если больше 4000 символов
    chunks = [output[i:i+4000] for i in range(0, len(output), 4000)]
    for chunk in chunks:
        await callback.message.answer(chunk)
    
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    users = await get_all_users()
    total = len(users)
    await callback.message.answer(f"📊 <b>Статистика:</b>\n\nВсего: {total}")
    await callback.answer()

@router.callback_query(F.data == "admin_fill_airports")
async def admin_fill_airports_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    
    try:
        airport_count = len(AIRPORTS)
        logger.info(f"🛫 AIRPORTS загружен: {airport_count} записей")
        await callback.message.answer(
            f"📋 <b>Загружено {airport_count} аэродромов</b>\n\n"
            f"⏳ Начинаю заполнение базы..."
        )
    except Exception as e:
        logger.error(f"❌ Ошибка доступа к AIRPORTS: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}")
        return
    
    await callback.answer()
    
    success_count = 0
    error_count = 0
    
    for i, (keyword, content) in enumerate(AIRPORTS, 1):
        try:
            await add_info(keyword, content)
            success_count += 1
            
            if i % 25 == 0:
                logger.info(f"✅ Прогресс: {i}/{airport_count}")
            
            await asyncio.sleep(0.03)
            
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Ошибка {keyword}: {e}")
    
    logger.info(f"✅ ЗАВЕРШЕНО! Успешно: {success_count}, Ошибок: {error_count}")
    
    await callback.message.answer(
        f"✅ <b>Заполнение завершено!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Ошибок: {error_count}\n\n"
        f"Теперь можно искать аэродромы через '📚 Полезная информация'"
    )

@router.callback_query(F.data == "admin_manage")
async def admin_manage_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    await callback.message.edit_text("👥 <b>Управление админами</b>", reply_markup=get_admin_manage_menu())
    await callback.answer()

@router.callback_query(F.data == "admin_add")
async def admin_add_callback(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin_check(callback.from_user.id):
        return
    await state.set_state(AdminStates.adding_admin)
    await callback.message.answer("➕ Введите User ID:")
    await callback.answer()

@router.callback_query(F.data == "admin_remove")
async def admin_remove_callback(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin_check(callback.from_user.id):
        return
    await state.set_state(AdminStates.removing_admin)
    await callback.message.answer("➖ Введите User ID для удаления:")
    await callback.answer()

@router.callback_query(F.data == "admin_list_all")
async def admin_list_all_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    admins = await get_all_admins()
    text = "🛡 <b>Админы:</b>\n\n"
    for i, admin in enumerate(admins, 1):
        text += f"{i}. <code>{admin['user_id']}</code>\n"
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "admin_menu_back")
async def admin_menu_back_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    await callback.message.edit_text("🛡 <b>Панель админа</b>", reply_markup=get_admin_menu())
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    await callback.message.answer("Выберите действие:", reply_markup=get_main_menu(is_admin=True))
    await callback.answer()

@router.message(AdminStates.adding_admin)
async def admin_add_process(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
        success, msg = await add_admin(target_id, message.from_user.id)
        await send_and_save(message, msg)
    except:
        await send_and_save(message, "❌ Ошибка формата")

@router.message(AdminStates.removing_admin)
async def admin_remove_process(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
        success, msg = await remove_admin(target_id, message.from_user.id)
        await send_and_save(message, msg)
    except:
        await send_and_save(message, "❌ Ошибка")

@router.message(Command("list"))
async def admin_list_cmd(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        return
    users = await get_all_users()
    output = "📋 <b>Список личного состава:</b>\n\n"
    for i, u in enumerate(users, 1):
        user_id = u['user_id']
        fio = u['fio']
        rank = u['rank']
        status_text = get_user_status_with_colors(u)
        
        output += f"{i}. 👤 {fio}\n"
        output += f"   Звание: {rank}\n"
        if u.get('qual_rank'):
            output += f"   Квалификация: {u['qual_rank']}\n"
        output += f"   {status_text}\n"
        output += f"   /user{user_id}\n\n"
    
    chunks = [output[i:i+4000] for i in range(0, len(output), 4000)]
    for chunk in chunks:
        await message.answer(chunk)

@router.message(Command("admin_menu"))
async def admin_menu_cmd(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        return
    await send_and_save(message, "🛡 <b>Панель админа</b>", reply_markup=get_admin_menu())

@router.message(Command("fill_airports"))
async def admin_fill_airports_cmd(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        return
    await send_and_save(message, "⏳ Заполняю...")
    count = 0
    for keyword, content in AIRPORTS:
        try:
            await add_info(keyword, content)
            count += 1
        except:
            pass
    await send_and_save(message, f"✅ Заполнено: {count} аэродромов")

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await state.clear()
    admin = is_admin_check(message.from_user.id)
    await send_and_save(
        message,
        "❌ Отменено",
        reply_markup=get_persistent_menu(is_admin=admin)
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await cleanup_last_bot_message(message)
    text = "ℹ️ <b>Помощь:</b>\n\n"
    text += "/start - Начать\n"
    text += "/help - Помощь\n"
    text += "/cancel - Отмена\n"
    if is_admin_check(message.from_user.id):
        text += "\n🛡 <b>Админ:</b>\n"
        text += "/list - Список\n"
        text += "/admin_menu - Меню\n"
        text += "/fill_airports - База"
    await send_and_save(message, text)

# ========== ПРОСМОТР ПОЛНОЙ АНКЕТЫ ПОЛЬЗОВАТЕЛЯ ==========

@router.message(F.text.startswith("/user"))
async def show_user_full_profile(message: types.Message):
    """Показывает полную анкету пользователя по команде /user{user_id}"""
    try:
        # Извлекаем user_id из команды /user123456789
        user_id = int(message.text.replace("/user", ""))
        user = await get_user(user_id)
        
        if not user:
            await send_and_save(message, "❌ Пользователь не найден")
            return
        
        # Формируем полную анкету
        text = f"👤 <b>ПОЛНАЯ АНКЕТА</b>\n\n"
        text += f"📋 <b>Основные данные:</b>\n"
        text += f"• ФИО: {user.get('fio', 'Не указано')}\n"
        text += f"• Звание: {user.get('rank', 'Не указано')}\n"
        text += f"• Квалификация: {user.get('qual_rank', 'Не указано')}\n\n"
        
        text += f"📅 <b>Сроки и документы:</b>\n"
        text += f"• Отпуск: {user.get('vacation_start', 'Не указано')} - {user.get('vacation_end', 'Не указано')}\n"
        text += f"• ВЛК: {user.get('vlk_date', 'Не пройдено')}\n"
        text += f"• УМО: {user.get('umo_date', 'Не пройдено')}\n\n"
        
        text += f"✈️ <b>КБП:</b>\n"
        text += f"• КБП-4 МД-М: {user.get('kbp_4_md_m', 'Не пройдено')}\n"
        text += f"• КБП-7 МД-М: {user.get('kbp_7_md_m', 'Не пройдено')}\n"
        text += f"• КБП-4 МД-90А: {user.get('kbp_4_md_90a', 'Не пройдено')}\n"
        text += f"• КБП-7 МД-90А: {user.get('kbp_7_md_90a', 'Не пройдено')}\n\n"
        
        text += f"🪂 <b>Прыжки:</b>\n"
        text += f"• Дата: {user.get('jumps_date', 'Не указано')}\n\n"
        
        # Добавляем статус с цветовой индикацией
        status_text = get_user_status_with_colors(user)
        text += f"\n{status_text}\n"
        
        # Кнопка назад
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_list")]
        ])
        
        await send_and_save(message, text, reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка показа анкеты: {e}")
        await send_and_save(message, "❌ Ошибка при загрузке анкеты")

# ========== ОБРАБОТКА ВСЕХ ТЕКСТОВЫХ СООБЩЕНИЙ (В САМОМ КОНЦЕ!) ==========

@router.message(F.text)
async def handle_any_text(message: types.Message, state: FSMContext):
    """Любое текстовое сообщение = возврат в меню, но только если нет активного состояния"""
    
    # Проверяем текущее состояние
    current_state = await state.get_state()
    
    # Если есть активное состояние — пропускаем
    if current_state is not None:
        return
    
    # Игнорируем ответы на сообщения бота
    if message.reply_to_message and message.reply_to_message.from_user.id == message.bot.id:
        return
    
    # Очищаем последнее сообщение бота
    await cleanup_last_bot_message(message)
    
    user = await get_user(message.from_user.id)
    admin = is_admin_check(message.from_user.id)
    
    if user and user.get('registered'):
        await send_and_save(
            message,
            "Добро пожаловать обратно! Выберите действие:",
            reply_markup=get_persistent_menu(is_admin=admin)
        )
    else:
        await send_and_save(
            message,
            "👋 Приветствую! Для доступа к функциям необходимо пройти регистрацию.",
            reply_markup=get_persistent_menu(is_admin=admin)
        )
