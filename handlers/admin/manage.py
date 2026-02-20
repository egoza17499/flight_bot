from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from states import AdminStates
from database import add_admin, remove_admin, get_all_admins
from keyboards import get_admin_menu, get_admin_manage_menu
from ..common import cleanup_last_bot_message, send_and_save, is_admin_check  # ✅ ..common

router = Router()

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
    await callback.message.answer("Выберите действие:", reply_markup=get_admin_menu(is_admin=True))
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
