from aiogram import Router, F, types
from aiogram.filters import Command
from database import get_all_users
from ..common import cleanup_last_bot_message, send_and_save, is_admin_check  # ✅ ..common вместо .common

router = Router()

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

@router.message(Command("list"))
async def admin_list_cmd(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        return
    users = await get_all_users()
    output = "📋 <b>Список:</b>\n\n"
    for u in users:
        output += f"👤 {u['fio']} ({u['rank']})\n"
    await send_and_save(message, output[:4000])
