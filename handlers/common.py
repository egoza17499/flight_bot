import logging
from aiogram import types
from config import ADMIN_ID
from utils import get_persistent_menu  # ✅ Импортируем из utils

logger = logging.getLogger(__name__)

# Хранение последних сообщений
last_bot_messages = {}
last_sent_results = {}

async def delete_message_safe(message: types.Message):
    """Безопасное удаление сообщения"""
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"Не удалось удалить сообщение: {e}")

async def cleanup_last_bot_message(message: types.Message):
    """Удаляет последнее сообщение бота в чате"""
    chat_id = message.chat.id
    if chat_id in last_bot_messages:
        try:
            await message.bot.delete_message(chat_id, last_bot_messages[chat_id])
        except Exception as e:
            logger.debug(f"Не удалось удалить старое сообщение: {e}")
        finally:
            if chat_id in last_bot_messages:
                del last_bot_messages[chat_id]

async def send_and_save(message: types.Message, text: str, **kwargs):
    """Отправляет сообщение и сохраняет его ID"""
    sent_message = await message.answer(text, **kwargs)
    last_bot_messages[message.chat.id] = sent_message.message_id
    return sent_message

def is_duplicate_result(chat_id: int, query: str, result_text: str) -> bool:
    """Проверяет является ли результат дубликатом"""
    if chat_id in last_sent_results:
        last_query, last_result = last_sent_results[chat_id]
        if query.lower() == last_query.lower() and result_text == last_result:
            return True
    return False

def save_search_result(chat_id: int, query: str, result_text: str):
    """Сохраняет последний результат поиска"""
    last_sent_results[chat_id] = (query, result_text)

def is_admin_check(user_id):
    """Проверяет является ли пользователь админом"""
    return user_id == ADMIN_ID
