from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user
from utils import generate_profile_text, check_flight_ban
from .common import cleanup_last_bot_message, send_and_save, is_admin_check, get_persistent_menu

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
