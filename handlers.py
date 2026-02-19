import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from database import add_user, update_user_field, set_registered, get_user, get_all_users, search_info
from states import Registration, EditProfile, SearchInfo
from keyboards import get_main_menu, get_edit_menu, FIELD_MAP
from utils import parse_date, generate_profile_text, check_flight_ban
from config import ADMIN_ID

router = Router()

# --- СТАРТ И РЕГИСТРАЦИЯ ---

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await add_user(message.from_user.id, message.from_user.username)
    user = await get_user(message.from_user.id)
    
    if user and user.get('registered'):
        await message.answer("Добро пожаловать обратно! Выберите действие:", reply_markup=get_main_menu())
    else:
        await message.answer("Приветствую! Для доступа к функциям необходимо пройти регистрацию.\nНачнем? (Напишите /start еще раз или просто начните вводить данные)")
        await state.set_state(Registration.fio)
        await message.answer("1️⃣ Введите вашу Фамилию Имя Отчество:")

@router.message(Registration.fio)
async def reg_fio(message: types.Message, state: FSMContext):
    await update_user_field(message.from_user.id, 'fio', message.text)
    await state.set_state(Registration.rank)
    await message.answer("2️⃣ Введите воинское звание:")

@router.message(Registration.rank)
async def reg_rank(message: types.Message, state: FSMContext):
    await update_user_field(message.from_user.id, 'rank', message.text)
    await state.set_state(Registration.qual_rank)
    await message.answer("3️⃣ Введите квалификационный разряд:")

@router.message(Registration.qual_rank)
async def reg_qual(message: types.Message, state: FSMContext):
    await update_user_field(message.from_user.id, 'qual_rank', message.text)
    await state.set_state(Registration.vacation)
    await message.answer("4️⃣ Введите даты крайнего отпуска (формат: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ):")

@router.message(Registration.vacation)
async def reg_vacation(message: types.Message, state: FSMContext):
    # Простая проверка формата, в идеале нужно парсить
    await update_user_field(message.from_user.id, 'vacation_start', message.text.split('-')[0].strip())
    await update_user_field(message.from_user.id, 'vacation_end', message.text.split('-')[1].strip())
    await state.set_state(Registration.vlk)
    await message.answer("5️⃣ Введите дату прохождения ВЛК (ДД.ММ.ГГГГ):")

@router.message(Registration.vlk)
async def reg_vlk(message: types.Message, state: FSMContext):
    await update_user_field(message.from_user.id, 'vlk_date', message.text)
    await state.set_state(Registration.umo)
    await message.answer("6️⃣ Введите дату прохождения УМО (ДД.ММ.ГГГГ). Если не было - напишите 'нет':")

@router.message(Registration.umo)
async def reg_umo(message: types.Message, state: FSMContext):
    val = message.text if message.text.lower() != 'нет' else None
    await update_user_field(message.from_user.id, 'umo_date', val)
    await state.set_state(Registration.kbp_4_md_m)
    await message.answer("7️⃣ КБП-4 Ил-76 МД-М (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_4_md_m)
async def reg_kbp4m(message: types.Message, state: FSMContext):
    await update_user_field(message.from_user.id, 'kbp_4_md_m', message.text)
    await state.set_state(Registration.kbp_7_md_m)
    await message.answer("8️⃣ КБП-7 Ил-76 МД-М (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_7_md_m)
async def reg_kbp7m(message: types.Message, state: FSMContext):
    await update_user_field(message.from_user.id, 'kbp_7_md_m', message.text)
    await state.set_state(Registration.kbp_4_md_90a)
    await message.answer("9️⃣ КБП-4 Ил-76 МД-90А (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_4_md_90a)
async def reg_kbp4_90(message: types.Message, state: FSMContext):
    await update_user_field(message.from_user.id, 'kbp_4_md_90a', message.text)
    await state.set_state(Registration.kbp_7_md_90a)
    await message.answer("🔟 КБП-7 Ил-76 МД-90А (ДД.ММ.ГГГГ):")

@router.message(Registration.kbp_7_md_90a)
async def reg_kbp7_90(message: types.Message, state: FSMContext):
    await update_user_field(message.from_user.id, 'kbp_7_md_90a', message.text)
    await state.set_state(Registration.jumps)
    await message.answer("1️⃣1️⃣ Дата выполнения прыжков с парашютом (ДД.ММ.ГГГГ):")

@router.message(Registration.jumps)
async def reg_finish(message: types.Message, state: FSMContext):
    await update_user_field(message.from_user.id, 'jumps_date', message.text)
    await set_registered(message.from_user.id)
    await state.clear()
    
    # Проверка банов сразу после регистрации
    user = await get_user(message.from_user.id)
    bans = check_flight_ban(user)
    
    if bans:
        ban_text = "\n".join(bans)
        await message.answer(f"⚠️ ВНИМАНИЕ!\n{ban_text}", reply_markup=get_main_menu())
    else:
        await message.answer("✅ Регистрация успешно завершена!", reply_markup=get_main_menu())
        
# --- ГЛАВНОЕ МЕНЮ ---

@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: types.Message):
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

@router.callback_query(F.data == "edit_start")
async def start_edit(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите параметр для редактирования:", reply_markup=get_edit_menu())

@router.callback_query(F.data.startswith("edit_"))
async def choose_field_edit(callback: types.CallbackQuery, state: FSMContext):
    field_key = callback.data.replace("edit_", "")
    # Находим человеческое название для подсказки
    human_name = [k for k, v in FIELD_MAP.items() if v == FIELD_MAP.get(field_key)][0] # Упрощено
    
    await state.set_state(EditProfile.entering_value)
    await state.update_data(edit_field=FIELD_MAP.get(field_key))
    await callback.message.edit_text(f"Введите новое значение для параметра.\nПример: ДД.ММ.ГГГГ")
    await callback.answer()

@router.message(EditProfile.entering_value)
async def save_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data.get('edit_field')
    if field:
        await update_user_field(message.from_user.id, field, message.text)
        await message.answer("✅ Данные обновлены!")
        await state.clear()
        await show_profile(message) # Показать обновленный профиль

@router.callback_query(F.data == "back_to_profile")
async def back_prof(callback: types.CallbackQuery):
    await callback.message.edit_text("Меню профиля", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад к профилю", callback_data="dummy")]]))
    # Тут лучше просто вызвать show_profile, но edit_text может конфликтовать, если сообщение уже другое. 
    # Для простоты отправим новое сообщение
    await callback.message.answer("Выберите действие:", reply_markup=get_main_menu())
    await callback.answer()

# --- ПОЛЕЗНАЯ ИНФОРМАЦИЯ ---

@router.message(F.text == "📚 Полезная информация")
async def start_search(message: types.Message, state: FSMContext):
    await state.set_state(SearchInfo.waiting_query)
    await message.answer("Напишите город или аэродром, информация по которому вас интересует:")

@router.message(SearchInfo.waiting_query)
async def process_search(message: types.Message, state: FSMContext):
    results = await search_info(message.text)
    if results:
        for res in results:
            await message.answer(res)
    else:
        await message.answer("Информация не найдена, извините.")
    await state.clear()

# --- АДМИНКА ---

@router.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = await get_all_users()
    if not users:
        await message.answer("Список пуст.")
        return
    
    output = "📋 <b>Список личного состава:</b>\n\n"
    for u in users:
        bans = check_flight_ban(u)
        line = f"👤 {u['fio']} ({u['rank']})"
        if bans:
            line += f"\n   ⚠️ <b>ПРОБЛЕМЫ:</b> {', '.join([b.split(': ')[1] for b in bans])}"
        output += line + "\n\n"
    
    # Если текст слишком длинный, телеграм обрежет. В продакшене нужно разбивать на части.
    await message.answer(output[:4000]) # Ограничение телеграма

@router.message(F.text) # Поиск админом по фамилии
async def admin_search_by_name(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Простой поиск: если текст не команда и не ответ боту
    users = await get_all_users()
    found = [u for u in users if message.text.lower() in u['fio'].lower()]
    
    if found:
        for u in found:
            text = generate_profile_text(u)
            await message.answer(text)
    # else ничего не делаем, чтобы не спамить в чат обычными сообщениями
