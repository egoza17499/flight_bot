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

def is_admin_check(user_id):
    """Проверяет является ли пользователь админом"""
    return user_id == ADMIN_ID

# ========== СТАРТ И РЕГИСТРАЦИЯ ==========

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await add_user(message.from_user.id, message.from_user.username)
    user = await get_user(message.from_user.id)
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
    try:
        if '-' not in message.text:
            await message.answer("❌ Неверный формат! Используйте: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ")
            return
        parts = message.text.split('-')
        if len(parts) != 2:
            await message.answer("❌ Ошибка формата! Введите две даты через дефис")
            return
        await update_user_field(message.from_user.id, 'vacation_start', parts[0].strip())
        await update_user_field(message.from_user.id, 'vacation_end', parts[1].strip())
        await state.set_state(Registration.vlk)
        await message.answer("5️⃣ Введите дату прохождения ВЛК (ДД.ММ.ГГГГ):")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

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
    await state.set_state(SearchInfo.waiting_query)
    await message.answer("🔍 Напишите город или аэродром, информация по которому вас интересует:")

@router.message(SearchInfo.waiting_query)
async def process_search(message: types.Message, state: FSMContext):
    results = await search_info(message.text)
    if results:
        for res in results:
            await message.answer(res)
    else:
        await message.answer("❌ Информация не найдена, извините.")
    await state.clear()

@router.message(F.text == "🛡 Функции админа")
async def admin_menu_button(message: types.Message):
    if not is_admin_check(message.from_user.id):
        await message.answer("❌ Доступ запрещен.")
        return
    await message.answer("🛡 <b>Панель администратора</b>\n\nВыберите действие:", reply_markup=get_admin_menu())

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
    await callback.message.edit_text(f"✏️ Введите значение для: <b>{field_name}</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
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
    data = await state.get_data()
    field_key = data.get('edit_field')
    if not field_key:
        await message.answer("❌ Ошибка")
        await state.clear()
        return
    if field_key == "vacation":
        parts = message.text.split('-')
        if len(parts) == 2:
            await update_user_field(message.from_user.id, 'vacation_start', parts[0].strip())
            await update_user_field(message.from_user.id, 'vacation_end', parts[1].strip())
            await message.answer("✅ Обновлено!")
    else:
        db_field = FIELD_MAP.get(field_key)
        if db_field:
            await update_user_field(message.from_user.id, db_field, message.text)
            await message.answer("✅ Обновлено!")
    await state.clear()
    await show_profile(message)

# ========== АДМИН ПАНЕЛЬ ==========

@router.callback_query(F.data == "admin_list")
async def admin_list_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    users = await get_all_users()
    output = "📋 <b>Список:</b>\n\n"
    for u in users:
        output += f"👤 {u['fio']} ({u['rank']})\n"
    await callback.message.answer(output[:4000])
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
    
    await callback.message.answer("⏳ Заполняю базу аэродромов...")
    
    airports = [
        ("Архангельск", "РЦ: 8-812-263-15-25"),
        ("Архангельск Талаги", "1) 8-818-263-15-25 (гр. АДП)\n2) 8-818-263-14-00 (ЦУА)\n3) 8-818-241-31-19 (АДП+)"),
        ("Алатырь", "в/ч 58661-83: 8-835-316-15-57"),
        ("Андриаполь", "8-482-673-13-64 (УС)"),
        ("Анадырь Угольный", "1) 8-427-325-56-87\n2) 8-421-241-85-32 (РЦ)"),
        ("Армавир", "1) 8-613-773-262\n2) 8-861-377-32-61 (УС)"),
        ("Ахтубинск", "1) 8-851-414-20-11 (АДП+)\n2) 8-851-414-22-94 (АДП)"),
        ("Астрахань Приволжский", "1) 8-851-239-37-31 (гр. АДП)\n2) 8-851-257-70-20 (АДП)"),
        ("Ашулук", "1) 8-851-257-70-20 (АДП)\n2) 8-851-257-10-57 (ОД)"),
        ("Анапа", "1) 8-861-332-37-35 (АДП)\n2) 8-861-333-30-38 (УС)"),
        ("Абакан", "8-390-228-25-34"),
        ("Алма-Аты", "8-727-290-27-01"),
        ("Амдерма Рогачево-2", "1) 8-495-514-05-81\n2) 8-921-484-65-44"),
        ("Апатиты", "1) 8-815-557-43-44\n2) 8-815-557-02-76"),
        ("Арзамас Миус", "8-908-762-22-62"),
        ("Багай-Барановка", "1) 8-845-936-06-90 (УС)\n2) 8-906-304-13-45"),
        ("Балашов", "1) 8-845-455-32-88 (УС)\n2) 8-963-112-44-14 (АДП)"),
        ("Барнаул Михайловка", "1) 8-385-224-44-40 (АДП)\n2) 8-385-254-32-82 (ПДСП)"),
        ("Байконур Крайний", "8-495-660-25-07"),
        ("Белая", "1) 8-983-416-66-05 (ОД)\n2) 8-999-422-38-71 (Дисп)"),
        ("Беслан", "1) 8-867-240-88-29 (АДП)\n2) 8-867-750-50-28"),
        ("Белгород", "1) 8-472-223-57-80 (АДП)\n2) 8-472-223-57-83"),
        ("Братск", "1) 8-395-332-23-82 (УС)\n2) 8-950-124-45-64"),
        ("Буденновск", "1) 8-865-592-12-71 (УС)\n2) 8-919-753-68-73 (ОД)"),
        ("Бутурлиновка", "1) 8-473-612-14-44 (АДП)\n2) 8-903-857-36-97"),
        ("Брянск", "8-483-272-25-72"),
        ("Бугульма", "1) 8-855-946-35-30 (АДП)\n2) 8-855-946-34-95"),
        ("Борисоглебск", "8-980-349-87-19"),
        ("Бельбек", "1) 118-142-240 (Дисп)\n2) 8-863-234-81-47"),
        ("Вологда Кипелово", "1) 8-817-255-15-51 (УС)\n2) 8-817-225-15-15"),
        ("Воздвиженка", "1) 8-914-650-36-63\n2) 8-914-793-13-71"),
        ("Воронеж", "1) 8-473-255-46-60\n2) 8-473-255-46-66"),
        ("Воронеж Придача", "8-473-249-90-46 (АДП)"),
        ("Владимир Семязино", "1) 8-492-277-85-13\n2) 8-492-277-85-12 (УС)"),
        ("Воркута Советский", "1) 8-821-513-63-89 (ДПЧ)\n2) 8-904-104-55-15 (АДП)"),
        ("Владивосток Кневичи", "1) 8-232-322-770 (АДП+)\n2) 8-914-717-97-19"),
        ("Владивосток Центральная Угловая", "8-914-979-36-31"),
        ("Волгоград Мариновка", "1) 8-844-726-10-33 (УС)\n2) 8-844-726-10-30"),
        ("Вязьма", "8-481-312-25-05"),
        ("Великие Луки", "1) 8-811-532-69-66 (МДП)\n2) 8-811-537-26-28"),
        ("Возжаевка", "1) 8-914-565-53-30\n2) 8-914-567-30-29"),
        ("Громово Саккола", "1) 8-913-799-02-46 (УС)\n2) 8-921-762-97-91"),
        ("Геленджик", "8-861-419-90-13"),
        ("Горно-Алтайск", "+7-388-224-75-12 (ПДСП)"),
        ("Домна", "1) 8-996-313-95-84 (АДП)\n2) 8-934-481-76-12"),
        ("Ейск", "1) 8-861-323-41-37 (АДП)\n2) 8-861-322-76-77 (ОД)"),
        ("Ермолино", "1) 8-484-396-61-30\n2) 8-484-386-26-78"),
        ("Екатеринбург Кольцово", "1) 8-343-375-80-11 (ЗЦ)\n2) 8-343-375-96-19 (ЦУА)"),
        ("Иваново Северный", "1) 8-493-237-33-52 (УС)\n2) 8-493-237-62-64 (АДП)"),
        ("Иваново Южный", "1) 8-493-293-34-12\n2) 8-493-225-59-79"),
        ("Йошкар-Ола", "1) 8-836-272-72-40 (АДП)\n2) 8-836-272-74-46"),
        ("Иркутск-2", "1) 8-395-232-29-08 (АДП)\n2) 8-395-248-18-04 (Метео)"),
        ("Иркутск", "1) 8-395-226-63-95 (ПДСА)\n2) 8-395-226-64-05"),
        ("Казань Юдино", "1) 8-843-571-88-54 (АДП)\n2) 8-843-570-98-03"),
        ("Казань Борисоглебское", "1) 8-843-533-41-22 (АДП)\n2) 8-843-267-87-01"),
        ("Канск", "1) 8-391-612-47-20\n2) 8-391-612-15-50"),
        ("Капустин Яр", "1) 8-851-402-18-45 (УС)\n2) 8-851-414-20-11 (ОД)"),
        ("Караганда", "1) 8-721-249-66-41\n2) 8-721-242-85-55 (ПДСП)"),
        ("Киров Победилово", "8-833-255-15-31\n8-833-269-67-45"),
        ("Клин", "8-926-873-66-56"),
        ("Комсомольск-на-Амуре Дземги", "1) 8-914-319-41-10 (АДП)\n2) 8-914-216-37-37 (ОД)"),
        ("Комсомольск-на-Амуре Хурба", "1) 8-984-176-93-17 (АДП)\n2) 8-914-318-26-53"),
        ("Крымск", "1) 8-861-312-16-34 (УС)\n2) 8-964-937-03-30 (АД)"),
        ("Калининград Храброво", "8-401-270-20-37\n8-401-261-04-65 (ПДСП)"),
        ("Калининград Чкаловск", "1) 8-401-250-28-25\n2) 8-401-221-58-36 (АДП+)"),
        ("Каменск-Уральский", "1) 8-343-936-57-57 (ОД)\n2) 8-982-715-31-91 (АДП)"),
        ("Кемерово", "1) 8-384-244-17-60\n2) 8-384-239-02-98 (ПДСП)"),
        ("Кострома", "8-494-235-76-91 (АДП)"),
        ("Кореновск", "8-918-956-57-14"),
        ("Красноярск", "1) 8-391-278-88-05\n2) 8-391-252-65-40 (АДП)"),
        ("Краснодар", "1) 8-967-650-70-35 (ОД)\n2) 8-909-452-22-60 (АДП)"),
        ("Крым Гвардейское", "1) 8-978-129-94-23 (АДП)\n2) 8-978-922-80-29 (РЦ)"),
        ("Крым Джанкой", "1) 8-978-835-35-09\n2) 8-987-090-88-87"),
        ("Кубинка", "1) 8-498-677-70-68 (УС)\n2) 8-495-992-29-52"),
        ("Кумертау", "1) 8-927-314-70-28\n2) 8-347-614-21-83"),
        ("Курск", "8-910-730-03-47 (АДП)"),
        ("Минск", "1) 8-017-219-29-53\n2) 8-017-222-59-73"),
        ("Нижний Новгород Стригино", "1) 8-831-269-35-20\n2) 8-831-261-80-90 (ПДСП)"),
        ("Оленегорск", "1) 8-911-801-07-20 (АДП)\n2) 8-911-309-36-17"),
        ("Петрозаводск", "1) 8-814-271-13-77\n2) 8-921-524-25-31 (АДП+)"),
        ("Рязань", "1) 8-915-614-40-00 (ОД)\n2) 8-491-233-53-18"),
        ("Салехард", "1) 8-349-227-44-04\n2) 8-349-227-42-23"),
        ("Сабетта", "8-495-231-16-34 (ПДСП)"),
        ("Санкт-Петербург", "8-812-305-17-51"),
        ("Тамбов", "8-915-880-58-80 (АД+)"),
        ("Украинка", "1) 8-914-576-24-91\n2) 8-996-384-37-95"),
        ("Ханты-Мансийск", "8-346-735-42-09"),
        ("Чита", "1) 8-302-241-20-55 (АДП)\n2) 8-924-510-01-10"),
        ("Шахты", "8-918-551-56-60"),
        ("Энгельс-2", "1) 8-999-539-35-00 (АДП+)\n2) 8-917-203-51-55"),
        ("Шагол", "1) 8-351-725-85-30 (ОД)\n2) 8-351-210-46-21 (УС)"),
        ("Шайковка", "1) 8-910-528-41-60 (АДП)\n2) 8-810-860-20-35"),
        ("Чебеньки", "8-922-552-85-54 (АДП)"),
        ("Южно-Сахалинск", "1) 8-424-278-87-74\n2) 8-424-278-83-42 (ПДСП)"),
        ("Челябинск", "1) +7-351-778-32-36 (ПДСП)\n2) 8-351-779-07-01 (АДП)"),
        ("Ярославль", "1) 8-485-243-18-38 (АДП)\n2) 8-485-243-18-37"),
        ("Чкаловский", "1) 8-495-993-59-09\n2) 8-963-678-25-32 (АДП)"),
        ("Ростов Платов", "276-70-27\n276-77-43\nПДСП: 333-47-80"),
        ("Чебоксары", "1) 8-835-230-11-76\n2) 8-835-230-11-55 (АДП)"),
        ("Хотилово", "1) 8-482-335-28-69 (ДПЧ)\n2) 8-482-332-01-32 (АДП+)"),
        ("Хабаровск", "1) 8-421-226-33-33\n2) 8-421-226-20-38"),
        ("Улан-Удэ", "1) 8-996-936-10-57 (АД)\n2) 8-301-225-15-00"),
        ("Ульяновск", "1) 8-842-261-88-75 (АДП)\n2) 8-842-258-84-00 (ПДСП)"),
        ("Уфа", "1) 8-347-279-18-73\n2) 8-347-229-55-97 (ПДСП)"),
        ("Таганрог", "1) 8-863-433-44-60 (ОД)\n2) 8-988-536-88-16 (АДП)"),
        ("Тверь", "1) 8-482-244-71-57 (ОД)\n2) 8-482-244-75-41 (УС)"),
        ("Тикси", "1) 8-924-360-80-34\n2) 8-914-287-91-26 (ОД)"),
        ("Томск", "8-382-293-27-01"),
        ("Тула", "1) 8-487-238-16-26 (ДПЧ)\n2) 8-487-238-17-83 (УС)"),
        ("Тюмень", "1) 8-345-249-64-50\n2) 8-345-249-64-98 (ПДСП)"),
        ("Саранск", "1) 8-834-246-24-43 (ПДСП)\n2) 8-834-246-24-96"),
        ("Севастополь", "8-978-819-79-87"),
        ("Сольцы", "1) 8-816-553-05-79 (УС)\n2) 8-911-602-53-89"),
        ("Старая Русса", "1) 8-816-523-67-28 (АДП)\n2) 8-911-620-85-32"),
        ("Сочи", "1) 8-862-249-75-71 (АДП+)\n2) 8-862-241-98-21"),
        ("Санкт-Петербург Пулково", "1) 8-812-704-36-64 (АДП)\n2) 8-812-324-34-63"),
        ("Североморск-1", "1) 8-815-376-41-76\n2) 8-815-376-40-03 (АД)"),
        ("Североморск-3", "1) 8-815-376-22-78\n2) 8-911-311-22-13"),
        ("Сургут", "8-346-277-04-14 (ПДСП)"),
        ("Сеща", "1) 8-483-329-75-05 (ОД)\n2) 8-980-315-14-39"),
        ("Самара", "1) 8-846-955-02-79\n2) 8-846-920-43-77 (метеo)"),
        ("Симферополь", "1) 8-365-259-52-80\n2) 8-365-259-53-99"),
        ("Саратов", "8-927-056-35-44 (диспетчер)"),
        ("Саваслейка", "1) 8-831-767-12-35 (УС)\n2) 8-951-908-18-70 (ОД)"),
        ("Сызрань", "1) 8-927-772-41-92\n2) 8-996-741-04-35 (АДП)"),
        ("Ростов", "1) 8-863-272-31-53\n2) 8-863-272-32-94"),
        ("Ртищево", "1) 8-917-303-28-23\n2) 8-987-829-37-23 (АДП+)"),
        ("Ржев", "8-482-326-64-82"),
        ("Петропавловск-Камчатский", "1) 8-415-316-73-21 (АДП)\n2) +7-924-685-40-71"),
        ("Плесецк", "1) 8-921-292-34-09 +\n2) 8-818-342-06-01"),
        ("Полярный", "1) 8-411-365-31-31\n2) 8-411-364-90-82 (АДП)"),
        ("Пермь", "1) 8-342-294-61-48 (УС)\n2) 8-992-203-88-15 (АДП)"),
        ("Псков", "8-811-262-02-67"),
        ("Омск", "1) 8-381-253-61-83 (АДП)\n2) 8-923-763-92-97"),
        ("Оренбург", "1) 8-353-276-51-07 (ОД)\n2) 8-353-276-51-62"),
        ("Орск", "1) 8-353-720-33-22 (АДП)\n2) 8-353-720-31-70 (ПДСП)"),
        ("Остафьево", "1) 8-969-348-98-11 (АДП+)\n2) 8-495-817-30-21"),
        ("Норильск", "1) 8-391-947-02-33 (АДП)\n2) 8-391-942-89-41 (ПДСА)"),
        ("Нижневартовск", "1) 8-346-649-20-30 (ПДСП)\n2) 8-912-934-83-64"),
        ("Новосибирск", "1) 8-383-279-09-85 (АДП)\n2) 8-383-216-94-67"),
        ("Нагурское", "1) 8-345-254-41-15\n2) 8-345-254-41-14"),
        ("Нижнекамск", "8-855-279-09-16 (ПДСП)"),
        ("Москва Внуково", "1) 8-495-436-74-51 (метеo)\n2) 8-495-956-87-48 (МЗЦ)"),
        ("Москва", "1) 8-495-268-44-70 (УС)\n2) 8-495-268-19-45 (ДС)"),
        ("Морозовск", "1) 8-863-844-31-46 (УС+)\n2) 8-928-817-45-75 (АДП)"),
        ("Мончегорск", "1) 8-815-363-15-24\n2) 8-911-302-92-97 (АДП)"),
        ("Моздок", "1) 8-867-363-23-00\n2) 8-960-404-38-01 (АДП+)"),
        ("Мирный", "1) 8-411-369-81-66\n2) 8-411-369-81-20"),
        ("Мичуринск", "8-474-278-21-60 (УС)"),
        ("Махачкала", "1) 8-872-298-88-27 (АДП+)\n2) 8-872-298-88-14 (ПДСП)"),
        ("Миллерово", "1) 8-863-852-37-57 (УС)\n2) 8-928-296-98-22"),
        ("Минеральные Воды", "1) 8-879-222-04-33\n2) 8-928-378-93-59 +"),
        ("Мурманск", "8-815-228-14-32"),
        ("Мулино", "1) 8-963-366-79-36 (диспетчер)\n2) 8-964-831-02-40 (РП)"),
        ("Кызыл", "1) 8-394-225-25-82\n2) 8-996-338-24-21"),
        ("Лаговушка", "1) 8-352-313-19-00\n2) 8-912-063-06-08 (РП)"),
        ("Липецк", "1) 8-904-294-20-37\n2) 8-904-283-01-86 (АДП+)"),
        ("Левашово", "1) 8-812-597-91-41 (ОД)\n2) 8-981-860-79-95 (ОД)"),
        ("Курган", "+7-912-830-79-96"),
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
            logger.error(f"Ошибка {keyword}: {e}")
    
    await callback.message.answer(
        f"✅ Заполнено!\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Ошибок: {error_count}"
    )
    await callback.answer()

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
    if not is_admin_check(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
        success, msg = await add_admin(target_id, message.from_user.id)
        await message.answer(msg)
    except:
        await message.answer("❌ Ошибка формата")

@router.message(AdminStates.removing_admin)
async def admin_remove_process(message: types.Message):
    if not is_admin_check(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
        success, msg = await remove_admin(target_id, message.from_user.id)
        await message.answer(msg)
    except:
        await message.answer("❌ Ошибка")

@router.message(Command("list"))
async def admin_list_cmd(message: types.Message):
    if not is_admin_check(message.from_user.id):
        return
    users = await get_all_users()
    output = "📋 <b>Список:</b>\n\n"
    for u in users:
        output += f"👤 {u['fio']} ({u['rank']})\n"
    await message.answer(output[:4000])

@router.message(Command("admin_menu"))
async def admin_menu_cmd(message: types.Message):
    if not is_admin_check(message.from_user.id):
        return
    await message.answer("🛡 <b>Панель админа</b>", reply_markup=get_admin_menu())

@router.message(Command("fill_airports"))
async def admin_fill_airports_cmd(message: types.Message):
    if not is_admin_check(message.from_user.id):
        return
    await message.answer("⏳ Заполняю...")
    # Добавьте базовые аэродромы
    await add_info("Москва", "1) 8-495-436-74-51 (метеo)\n2) 8-495-956-87-48 (МЗЦ)")
    await add_info("Санкт-Петербург", "1) 8-812-704-36-64 (АДП)\n2) 8-812-324-34-63")
    await message.answer("✅ Готово!")

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_main_menu(is_admin=is_admin_check(message.from_user.id)))

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = "ℹ️ <b>Помощь:</b>\n\n"
    text += "/start - Начать\n"
    text += "/help - Помощь\n"
    text += "/cancel - Отмена\n"
    if is_admin_check(message.from_user.id):
        text += "\n🛡 <b>Админ:</b>\n"
        text += "/list - Список\n"
        text += "/admin_menu - Меню\n"
        text += "/fill_airports - База"
    await message.answer(text)
