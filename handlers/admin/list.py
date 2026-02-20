from aiogram import Router, F, types
from aiogram.filters import Command
from database import get_all_users
from utils import get_user_status_with_colors
from ..common import cleanup_last_bot_message, send_and_save, is_admin_check

router = Router()

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
        fio = u.get('fio', 'Нет данных')
        rank = u.get('rank', '')
        status = get_user_status_with_colors(u)
        
        output += f"{i}. 👤 {fio} ({rank})\n"
        output += f"   {status}\n\n"
    
    await callback.message.answer(output[:4000])
    await callback.answer()

@router.message(Command("list"))
async def admin_list_cmd(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        return
    
    users = await get_all_users()
    if not users:
        await send_and_save(message, "📋 Список пуст.")
        return
    
    output = "📋 <b>Список личного состава:</b>\n\n"
    for i, u in enumerate(users, 1):
        fio = u.get('fio', 'Нет данных')
        rank = u.get('rank', '')
        status = get_user_status_with_colors(u)
        
        output += f"{i}. 👤 {fio} ({rank})\n"
        output += f"   {status}\n\n"
    
    await send_and_save(message, output[:4000])
