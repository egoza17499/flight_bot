from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from states import EditProfile
from database import get_user, update_user_field
from utils import generate_profile_text, check_flight_ban
from keyboards import get_edit_menu, FIELD_MAP, FIELD_NAMES
from .common import cleanup_last_bot_message, send_and_save

router = Router()

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
