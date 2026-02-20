from aiogram import Router, F, types
from database import get_all_users
from ..common import is_admin_check  # ✅ Две точки для подъема на уровень выше

router = Router()

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    users = await get_all_users()
    total = len(users)
    await callback.message.answer(f"📊 <b>Статистика:</b>\n\nВсего: {total}")
    await callback.answer()
