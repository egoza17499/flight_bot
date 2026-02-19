from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import get_all_users
from utils import parse_date, check_status
from config import ADMIN_ID
import asyncio

async def send_notification(bot, user_id, text):
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def check_deadlines(bot):
    users = await get_all_users()
    today_str = "сегодня" # Логика упрощена для примера
    
    # Дни для проверки: 30, 14, 7, 0
    check_days = [30, 14, 7, 0]
    
    for user in users:
        user_id = user['user_id']
        fio = user['fio']
        
        # Словарь полей для проверки
        fields_to_check = {
            'vlk_date': ('ВЛК', 6),
            'kbp_4_md_m': ('КБП-4 МД-М', 6),
            'kbp_7_md_m': ('КБП-7 МД-М', 12),
            'jumps_date': ('Прыжки', 12),
            # ... добавить остальные
        }

        for field, (name, limit_months) in fields_to_check.items():
            date_val = parse_date(user.get(field))
            if not date_val: continue
            
            days_left = (date_val - parse_date("01.01.2000")).days # Заглушка, нужна реальная логика diff
            
            # Реальная логика diff (упрощенная)
            from datetime import datetime
            delta = date_val - datetime.now().date()
            days = delta.days
            
            if days in check_days:
                msg_user = f"⚠️ {fio}, через {days if days > 0 else 0} дней истекает срок: {name}"
                msg_admin = f"🚨 Админ: У {fio} через {days if days > 0 else 0} дней выходит {name}"
                
                await send_notification(bot, user_id, msg_user)
                await send_notification(bot, ADMIN_ID, msg_admin)

def start_scheduler(bot):
    scheduler = AsyncIOScheduler()
    # Запуск проверки каждый день в 9:00
    scheduler.add_job(check_deadlines, CronTrigger(hour=9, minute=0), args=[bot])
    scheduler.start()
    return scheduler