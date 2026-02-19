import os  # ✅ Добавлен импорт!
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

logging.basicConfig(level=logging.INFO)

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
    
    logging.info(f"✅ Web server started on port {port}")
    logging.info(f"✅ Health check: http://localhost:{port}/health")

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    dp.include_router(router)
    
    # Инициализация базы данных
    await init_db()
    
    # Удаляем webhook (если был установлен)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск простого веб-сервера для Render (чтобы не было ошибок)
    await start_web_server()
    
    # Запуск планировщика уведомлений
    start_scheduler(bot)
    
    # Запуск polling (опрос Telegram)
    logging.info("🚀 Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("❌ Bot stopped by user")
