import asyncio
import os
import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

# ========== ПРОВЕРКА АДМИНА ==========

def is_admin_check(user_id):
    """Проверяет является ли пользователь админом"""
    return user_id == ADMIN_ID

# ========== СТАРТ И РЕГИСТРАЦИЯ ==========

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    await add_user(message.from_user.id, message.from_user.username)
    user = await get_user(message.from_user.id)
    
    # Проверяем админа
    admin = is_admin_check(message.from_user.id)
    
    if user and user.get('registered'):
        await message.answer(
            "Добро пожаловать обратно! Выберите действие:",
            reply_markup=get_main_menu(is_admin=admin)
        )
    else:
        await message.answer(
            "👋 Приветствую! Для доступа к функциям необходимо пройти регистрацию.\n\n"
            "Начнем? (Напишите /start еще раз или просто начните вводить данные)"
        )
        await state.set_state(Registration.fio)
        await message.answer("1️⃣ Введите вашу Фамилию Имя Отчество:")

@router.message(Registration.fio)
async def reg_fio(message: types.Message, state: FSMContext):
    """Регистрация: ФИО"""
    await update_user_field(message.from_user.id, 'fio', message.text)
    await state.set_state(Registration.rank)
    await message.answer("2️⃣ Введите воинское звание:")

@router.message(Registration.rank)
async def reg_rank(message: types.Message, state: FSMContext):
    """Регистрация: Звание"""
    await update_user_field(message.from_user.id, 'rank', message.text)
    await state.set_state(Registration.qual_rank)
    await message.answer("3️⃣ Введите квалификационный разряд:")

@router.message(Registration.qual_rank)
async def reg_qual(message: types.Message, state: FSMContext):
    """Регистрация: Квалификация"""
    await update_user_field(message.from_user.id, 'qual_rank', message.text)
    await state.set_state(Registration.vacation)
    await message.answer("4️⃣ Введите даты крайнего отпуска (формат: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ):")

@router.message(Registration.vacation)
async def reg_vacation(message: types.Message, state: FSMContext):
    """Регистрация: Отпуск"""
    try:
        if '-' not in message.text:
            await message.answer("❌ Неверный формат! Используйте: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ\nНапример: 01.06.2025 - 01.07.2025")
            return
        
        parts = message.text.split('-')
        if len(parts) != 2:
            await message.answer("❌ Ошибка формата! Введите две даты через дефис: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ")
            return
        
        vacation_start = parts[0].strip()
        vacation_end = parts[1].strip()
        
        if len(vacation_start) != 10 or len(vacation_end) != 10:
            await message.answer("❌ Даты должны быть в формате ДД.ММ.ГГГГ")
            return
        
        await update_user_field(message.from_user.id, 'vacation_start', vacation_start)
        await update_user_field(message.from_user.id, 'vacation_end', vacation_end)
        
        await state.set_state(Registration.vlk)
        await message.answer("5️⃣ Введите дату прохождения ВЛК (ДД.ММ.ГГГГ):")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\nПопробуйте еще раз в формате: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ")

@router.message(Registration.vlk)
async def reg_vlk(message: types.Message, state: FSMContext):
    """Регистрация: ВЛК"""
    await update_user_field(message.from_user.id, 'vlk_date', message.text)
    await state.set_state(Registration.umo)
    await message.answer("6️⃣ Введите дату прохождения УМО (ДД.ММ.ГГГГ). Если не было - напишите 'нет':")

@router.message(Registration.umo)
async def reg_umo(message: types.Message, state: FSMContext):
    """Регистрация: УМО"""
    val = message.text if message.text.lower() != 'нет' else None
    await update_user_field(message.from_user.id, 'umo_date', val)
    await state.set_state(Registration.kbp_4_md_m)
    await message.answer("7️⃣ КБП-4 Ил-76 МД-М (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_4_md_m)
async def reg_kbp4m(message: types.Message, state: FSMContext):
    """Регистрация: КБП-4 МД-М"""
    await update_user_field(message.from_user.id, 'kbp_4_md_m', message.text)
    await state.set_state(Registration.kbp_7_md_m)
    await message.answer("8️⃣ КБП-7 Ил-76 МД-М (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_7_md_m)
async def reg_kbp7m(message: types.Message, state: FSMContext):
    """Регистрация: КБП-7 МД-М"""
    await update_user_field(message.from_user.id, 'kbp_7_md_m', message.text)
    await state.set_state(Registration.kbp_4_md_90a)
    await message.answer("9️⃣ КБП-4 Ил-76 МД-90А (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_4_md_90a)
async def reg_kbp4_90(message: types.Message, state: FSMContext):
    """Регистрация: КБП-4 МД-90А"""
    await update_user_field(message.from_user.id, 'kbp_4_md_90a', message.text)
    await state.set_state(Registration.kbp_7_md_90a)
    await message.answer("🔟 КБП-7 Ил-76 МД-90А (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_7_md_90a)
async def reg_kbp7_90(message: types.Message, state: FSMContext):
    """Регистрация: КБП-7 МД-90А"""
    await update_user_field(message.from_user.id, 'kbp_7_md_90a', message.text)
    await state.set_state(Registration.jumps)
    await message.answer("1️⃣1️⃣ Дата выполнения прыжков с парашютом (ДД.ММ.ГГГГ):")

@router.message(Registration.jumps)
async def reg_finish(message: types.Message, state: FSMContext):
    """Регистрация: Завершение"""
    await update_user_field(message.from_user.id, 'jumps_date', message.text)
    await set_registered(message.from_user.id)
    await state.clear()
    
    user = await get_user(message.from_user.id)
    bans = check_flight_ban(user)
    
    admin = is_admin_check(message.from_user.id)
    
    if bans:
        ban_text = "\n".join(bans)
        await message.answer(f"⚠️ ВНИМАНИЕ!\n{ban_text}", reply_markup=get_main_menu(is_admin=admin))
    else:
        await message.answer("✅ Регистрация успешно завершена!", reply_markup=get_main_menu(is_admin=admin))

# ========== ГЛАВНОЕ МЕНЮ ==========

@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: types.Message):
    """Показать профиль пользователя"""
    user = await get_user(message.from_user.id)
    if not user or not user.get('registered'):
        await message.answer("Сначала пройдите регистрацию (/start)")
        return
    
    text = generate_profile_text(user)
    bans = check_flight_ban(user)
    
    if bans:
        text += "\n\n🚫 <b>ПОЛЕТЫ ЗАПРЕЩЕНЫ!</b>\n" + "\n".join(bans)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_start")]])
    await message.answer(text, reply_markup=kb)

@router.message(F.text == "📚 Полезная информация")
async def start_search(message: types.Message, state: FSMContext):
    """Начать поиск информации"""
    await state.set_state(SearchInfo.waiting_query)
    await message.answer("🔍 Напишите город или аэродром, информация по которому вас интересует:")

@router.message(SearchInfo.waiting_query)
async def process_search(message: types.Message, state: FSMContext):
    """Обработка поискового запроса"""
    results = await search_info(message.text)
    if results:
        for res in results:
            await message.answer(res)
    else:
        await message.answer("❌ Информация не найдена, извините.")
    await state.clear()

@router.message(F.text == "🛡 Функции админа")
async def admin_menu_button(message: types.Message):
    """Кнопка админ-панели"""
    if not is_admin_check(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Эта кнопка только для администратора.")
        return
    
    await message.answer(
        "🛡 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )

# ========== РЕДАКТИРОВАНИЕ ПРОФИЛЯ ==========

@router.callback_query(F.data == "edit_start")
async def start_edit(callback: types.CallbackQuery):
    """Начать редактирование профиля"""
    await callback.message.edit_text("✏️ Выберите параметр для редактирования:", reply_markup=get_edit_menu())
    await callback.answer()

@router.callback_query(F.data.startswith("edit_"))
async def choose_field_edit(callback: types.CallbackQuery, state: FSMContext):
    """Выбор поля для редактирования"""
    field_key = callback.data.replace("edit_", "")
    field_name = FIELD_NAMES.get(field_key, field_key)
    
    await state.set_state(EditProfile.entering_value)
    await state.update_data(edit_field=field_key)
    
    kb = [[InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_profile")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    
    await callback.message.edit_text(
        f"✏️ Введите новое значение для: <b>{field_name}</b>\n\n"
        f"Пример формата указан выше.",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к профилю"""
    await state.clear()
    user = await get_user(callback.from_user.id)
    if user and user.get('registered'):
        text = generate_profile_text(user)
        bans = check_flight_ban(user)
        if bans:
            text += "\n\n🚫 <b>ПОЛЕТЫ ЗАПРЕЩЕНЫ!</b>\n" + "\n".join(bans)
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_start")]])
        await callback.message.answer(text, reply_markup=kb)
    else:
        await callback.message.answer("Выберите действие:", reply_markup=get_main_menu(is_admin=is_admin_check(callback.from_user.id)))
    await callback.answer()

@router.message(EditProfile.entering_value)
async def save_edit(message: types.Message, state: FSMContext):
    """Сохранение отредактированных данных"""
    data = await state.get_data()
    field_key = data.get('edit_field')
    
    if not field_key:
        await message.answer("❌ Ошибка: поле не выбрано. Начните редактирование заново.")
        await state.clear()
        return
    
    if field_key == "vacation":
        try:
            parts = message.text.split('-')
            if len(parts) != 2:
                await message.answer("❌ Неверный формат. Используйте: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ")
                return
            await update_user_field(message.from_user.id, 'vacation_start', parts[0].strip())
            await update_user_field(message.from_user.id, 'vacation_end', parts[1].strip())
            await message.answer("✅ Даты отпуска обновлены!")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    else:
        db_field = FIELD_MAP.get(field_key)
        if db_field:
            await update_user_field(message.from_user.id, db_field, message.text)
            await message.answer("✅ Данные обновлены!")
        else:
            await message.answer("❌ Ошибка: неизвестное поле.")
    
    await state.clear()
    await show_profile(message)

# ========== АДМИН ПАНЕЛЬ ==========

@router.callback_query(F.data == "admin_list")
async def admin_list_callback(callback: types.CallbackQuery):
    """Список личного состава"""
    if not is_admin_check(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    users = await get_all_users()
    if not users:
        await callback.message.answer("Список пуст.")
        return
    
    output = "📋 <b>Список личного состава:</b>\n\n"
    for u in users:
        bans = check_flight_ban(u)
        line = f"👤 {u['fio']} ({u['rank']})"
        if bans:
            line += f"\n   ⚠️ <b>ПРОБЛЕМЫ:</b> {', '.join([b.split(': ')[1] for b in bans])}"
        output += line + "\n\n"
    
    await callback.message.answer(output[:4000])
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    """Статистика базы данных"""
    if not is_admin_check(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    users = await get_all_users()
    total = len(users)
    
    banned_count = 0
    for u in users:
        if check_flight_ban(u):
            banned_count += 1
    
    await callback.message.answer(
        f"📊 <b>Статистика базы данных:</b>\n\n"
        f"👥 Всего пользователей: {total}\n"
        f"✅ Готовы к полетам: {total - banned_count}\n"
        f"🚫 Имеют запреты: {banned_count}\n"
        f"📈 Процент готовности: {round((total - banned_count) / total * 100) if total > 0 else 0}%"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_fill_airports")
async def admin_fill_airports_callback(callback: types.CallbackQuery):
    """Заполнение базы аэродромов"""
    if not is_admin_check(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.answer("⏳ Начинаю заполнение базы аэродромов... Это может занять несколько минут.")
    
    airports = [
        ("Архангельск", "РЦ: 8-812-263-15-25"),
        ("Архангельск Талаги", "1) 8-818-263-15-25 (гр. АДП)\n2) 8-818-263-14-00 (ЦУА)"),
        ("Анадырь Угольный", "1) 8-427-325-56-87\n2) 8-421-241-85-32 (РЦ)"),
        ("Москва Внуково", "1) 8-495-436-74-51 (метеo)\n2) 8-495-956-87-48 (МЗЦ)"),
        ("Санкт-Петербург Пулково", "1) 8-812-704-36-64 (АДП)\n2) 8-812-324-34-63 +"),
        ("Нижний Новгород Стригино", "1) 8-831-269-35-20\n2) 8-831-261-80-90 (ПДСП)"),
        ("Екатеринбург Кольцово", "1) 8-343-375-80-11 (ЗЦ)\n2) 8-343-375-96-19 (ЦУА)"),
    ]
    
    success_count = 0
    error_count = 0
    
    for keyword, content in airports:
        try:
            await add_info(keyword, content)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            error_count += 1
            logger.error(f"Ошибка при добавлении {keyword}: {e}")
    
    await callback.message.answer(
        f"✅ Заполнение завершено!\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Ошибок: {error_count}"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_manage")
async def admin_manage_callback(callback: types.CallbackQuery):
    """Управление админами"""
    if not is_admin_check(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👥 <b>Управление администраторами</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_manage_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add")
async def admin_add_callback(callback: types.CallbackQuery, state: FSMContext):
    """Добавление админа"""
    if not is_admin_check(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await state.set_state(AdminStates.adding_admin)
    await callback.message.answer(
        "➕ <b>Добавление администратора</b>\n\n"
        "Отправьте <b>User ID</b> пользователя, которого хотите сделать админом.\n\n"
        "💡 Как узнать ID:\n"
        "- Пользователь пишет боту /start\n"
        "- В логах будет: <code>user_id=123456789</code>\n\n"
        "🔙 /admin_menu - отмена"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_remove")
async def admin_remove_callback(callback: types.CallbackQuery, state: FSMContext):
    """Удаление админа"""
    if not is_admin_check(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await state.set_state(AdminStates.removing_admin)
    await callback.message.answer(
        "➖ <b>Удаление администратора</b>\n\n"
        "Отправьте <b>User ID</b> админа для удаления.\n\n"
        "⚠️ <b>Внимание:</b>\n"
        "- Нельзя удалить себя\n"
        "- Нельзя удалить главного админа\n\n"
        "🔙 /admin_menu - отмена"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_list_all")
async def admin_list_all_callback(callback: types.CallbackQuery):
    """Список всех админов"""
    if not is_admin_check(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    admins = await get_all_admins()
    
    if not admins:
        await callback.message.answer("❌ Администраторы не найдены")
        await callback.answer()
        return
    
    text = "🛡 <b>Список администраторов:</b>\n\n"
    for i, admin in enumerate(admins, 1):
        user_id = admin['user_id']
        added_by = admin['added_by']
        added_at = admin['added_at'].strftime("%d.%m.%Y %H:%M")
        
        if user_id == ADMIN_ID:
            badge = "👑"
        else:
            badge = "🛡"
        
        text += f"{i}. {badge} <code>{user_id}</code>\n"
        text += f"   Добавлен: {added_at}\n"
        if added_by != 0:
            text += f"   Добавил: <code>{added_by}</code>\n"
        text += "\n"
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "admin_menu_back")
async def admin_menu_back_callback(callback: types.CallbackQuery):
    """Вернуться в адменку"""
    if not is_admin_check(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🛡 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: types.CallbackQuery):
    """Вернуться в главное меню"""
    if not is_admin_check(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.answer(
        "Добро пожаловать обратно! Выберите действие:",
        reply_markup=get_main_menu(is_admin=True)
    )
    await callback.answer()

# ========== ОБРАБОТКА СОСТОЯНИЙ АДМИНА ==========

@router.message(AdminStates.adding_admin)
async def admin_add_process(message: types.Message):
    """Процесс добавления админа"""
    if not is_admin_check(message.from_user.id):
        return
    
    try:
        target_id = int(message.text.strip())
        success, msg = await add_admin(target_id, message.from_user.id)
        await message.answer(msg)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите числовой ID.")

@router.message(AdminStates.removing_admin)
async def admin_remove_process(message: types.Message):
    """Процесс удаления админа"""
    if not is_admin_check(message.from_user.id):
        return
    
    try:
        target_id = int(message.text.strip())
        success, msg = await remove_admin(target_id, message.from_user.id)
        await message.answer(msg)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите числовой ID.")

# ========== КОМАНДЫ АДМИНА ==========

@router.message(Command("list"))
async def admin_list_cmd(message: types.Message):
    """Команда /list для админа"""
    if not is_admin_check(message.from_user.id):
        return
    
    users = await get_all_users()
    output = "📋 <b>Список личного состава:</b>\n\n"
    for u in users:
        bans = check_flight_ban(u)
        line = f"👤 {u['fio']} ({u['rank']})"
        if bans:
            line += f"\n   ⚠️ <b>ПРОБЛЕМЫ:</b> {', '.join([b.split(': ')[1] for b in bans])}"
        output += line + "\n\n"
    
    await message.answer(output[:4000])

@router.message(Command("admin_menu"))
async def admin_menu_cmd(message: types.Message):
    """Команда /admin_menu"""
    if not is_admin_check(message.from_user.id):
        return
    await message.answer(
        "🛡 <b>Панель администратора</b>",
        reply_markup=get_admin_menu()
    )

@router.message(Command("fill_airports"))
async def admin_fill_airports_cmd(message: types.Message):
    """Команда /fill_airports"""
    if not is_admin_check(message.from_user.id):
        return
    
    await message.answer("⏳ Начинаю заполнение базы аэродромов...")
    
    airports = [
        ("Архангельск", "РЦ: 8-812-263-15-25"),
        ("Москва Внуково", "1) 8-495-436-74-51 (метеo)"),
        ("Санкт-Петербург Пулково", "1) 8-812-704-36-64 (АДП)"),
    ]
    
    success_count = 0
    for keyword, content in airports:
        try:
            await add_info(keyword, content)
            success_count += 1
        except:
            pass
    
    await message.answer(f"✅ Заполнено: {success_count} аэродромов")

# ========== ОТМЕНА ДЕЙСТВИЙ ==========

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    admin = is_admin_check(message.from_user.id)
    await message.answer("❌ Действие отменено", reply_markup=get_main_menu(is_admin=admin))

# ========== ПОМОЩЬ ==========

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка по командам"""
    text = "ℹ️ <b>Справка по командам:</b>\n\n"
    text += "👤 <b>Для всех:</b>\n"
    text += "/start - Начать работу\n"
    text += "/help - Эта справка\n"
    text += "/cancel - Отменить действие\n\n"
    
    if is_admin_check(message.from_user.id):
        text += "🛡 <b>Для админа:</b>\n"
        text += "/list - Список личного состава\n"
        text += "/admin_menu - Панель админа\n"
        text += "/fill_airports - Заполнить базу аэродромов\n"
    
    await message.answer(text)
