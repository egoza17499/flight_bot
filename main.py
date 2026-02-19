import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database import init_db
from handlers import router
from scheduler import start_scheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint для Render"""
    return web.json_response({'status': 'ok', 'service': 'telegram-bot'})

async def start_web_server():
    """Запуск простого HTTP сервера для Render"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Получаем порт из переменных окружения или используем 8080
    port = int(os.getenv('PORT', 8080))
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✅ Web-сервер запущен на порту {port}")
    logger.info(f"✅ Проверка: http://localhost:{port}/health")

async def main():
    """Основная функция запуска бота"""
    logger.info("🚀 Запуск бота...")
    
    # Создаем бота и диспетчер
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Подключаем роутер с обработчиками
    dp.include_router(router)
    
    # Инициализация базы данных
    logger.info("📊 Инициализация базы данных...")
    await init_db()
    logger.info("✅ База данных готова")
    
    # 🔴 ВАЖНО: Удаляем webhook (чтобы не было конфликтов с polling)
    logger.info("🔄 Удаляем webhook...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook удален")
    
    # Запуск веб-сервера для Render (health check)
    logger.info("🌐 Запуск веб-сервера...")
    await start_web_server()
    
    # Запуск планировщика уведомлений
    logger.info("⏰ Запуск планировщика...")
    start_scheduler(bot)
    logger.info("✅ Планировщик запущен")
    
    # Запуск polling (опрос Telegram)
    logger.info("🤖 Запуск опроса бота...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка polling: {e}")
    finally:
        await bot.session.close()
        logger.info("🛑 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("❌ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
