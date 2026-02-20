import asyncio
import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from database import add_info, get_all_users
from airports_data import AIRPORTS
from ..common import is_admin_check, cleanup_last_bot_message, send_and_save  # ✅ Исправлен импорт

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == "admin_fill_airports")
async def admin_fill_airports_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    
    try:
        airport_count = len(AIRPORTS)
        logger.info(f"🛫 AIRPORTS загружен: {airport_count} записей")
        await callback.message.answer(
            f"📋 <b>Загружено {airport_count} аэродромов</b>\n\n"
            f"⏳ Начинаю заполнение базы..."
        )
    except Exception as e:
        logger.error(f"❌ Ошибка доступа к AIRPORTS: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}")
        return
    
    await callback.answer()
    
    success_count = 0
    error_count = 0
    
    for i, (keyword, content) in enumerate(AIRPORTS, 1):
        try:
            await add_info(keyword, content)
            success_count += 1
            
            if i % 25 == 0:
                logger.info(f"✅ Прогресс: {i}/{airport_count}")
            
            await asyncio.sleep(0.03)
            
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Ошибка {keyword}: {e}")
    
    logger.info(f"✅ ЗАВЕРШЕНО! Успешно: {success_count}, Ошибок: {error_count}")
    
    await callback.message.answer(
        f"✅ <b>Заполнение завершено!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Ошибок: {error_count}\n\n"
        f"Теперь можно искать аэродромы через '📚 Полезная информация'"
    )

@router.message(Command("fill_airports"))
async def admin_fill_airports_cmd(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        return
    await send_and_save(message, "⏳ Заполняю...")
    count = 0
    for keyword, content in AIRPORTS:
        try:
            await add_info(keyword, content)
            count += 1
        except:
            pass
    await send_and_save(message, f"✅ Заполнено: {count} аэродромов")
