from aiogram import Router, F, types
from database import get_all_users
from utils import check_flight_ban
from ..common import is_admin_check  # ✅ ..common

router = Router()

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    users = await get_all_users()
    total = len(users)
    banned = sum(1 for u in users if check_flight_ban(u))
    await callback.message.answer(
        f"📊 <b>Статистика:</b>\n\n"
        f"👥 Всего: {total}\n"
        f"✅ Готовы: {total - banned}\n"
        f"🚫 Запреты: {banned}"
    )
    await callback.answer()
