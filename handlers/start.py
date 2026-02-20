from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import add_user, get_user, update_user_field, set_registered
from states import Registration
from utils import check_flight_ban, get_persistent_menu
from config import ADMIN_ID
from .common import cleanup_last_bot_message, send_and_save, is_admin_check

router = Router()

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
