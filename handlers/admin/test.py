import logging
from aiogram import Router, types
from aiogram.filters import Command
from airports_data import AIRPORTS
from database import get_all_users
from ..common import cleanup_last_bot_message, send_and_save

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("test_airports"))
async def test_airports(message: types.Message):
    """Тестовая команда для проверки AIRPORTS"""
    await cleanup_last_bot_message(message)
    try:
        count = len(AIRPORTS)
        first = AIRPORTS[0] if count > 0 else None
        last = AIRPORTS[-1] if count > 0 else None
        await send_and_save(
            message,
            f"✅ <b>AIRPORTS работает!</b>\n\n"
            f"📊 <b>Всего аэродромов:</b> {count}\n"
            f"📍 <b>Первый:</b> {first[0] if first else 'N/A'}\n"
            f"📍 <b>Последний:</b> {last[0] if last else 'N/A'}\n\n"
            f"🔍 <b>Тип данных:</b> {type(AIRPORTS).__name__}"
        )
        logger.info(f"✅ Тест AIRPORTS: {count} записей")
    except Exception as e:
        await send_and_save(message, f"❌ <b>Ошибка:</b> {e}")
        logger.error(f"❌ Ошибка теста AIRPORTS: {e}")

@router.message(Command("test_db"))
async def test_db(message: types.Message):
    """Тест подключения к базе данных"""
    await cleanup_last_bot_message(message)
    try:
        users = await get_all_users()
        await send_and_save(
            message,
            f"✅ <b>База данных работает!</b>\n\n"
            f"📊 <b>Пользователей:</b> {len(users)}"
        )
        logger.info(f"✅ Тест БД: {len(users)} пользователей")
    except Exception as e:
        await send_and_save(message, f"❌ <b>Ошибка БД:</b> {e}")
        logger.error(f"❌ Ошибка теста БД: {e}")
