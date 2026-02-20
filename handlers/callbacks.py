from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, update_user_field
from states import EditProfile
from keyboards import get_edit_menu, get_admin_menu, get_admin_manage_menu
from utils import generate_profile_text, check_flight_ban, FIELD_MAP, FIELD_NAMES
from .common import cleanup_last_bot_message, send_and_save, is_admin_check, get_persistent_menu

router = Router()

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
