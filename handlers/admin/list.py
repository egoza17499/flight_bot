from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_all_users
from utils import get_user_status_with_colors
from ..common import is_admin_check, cleanup_last_bot_message, send_and_save
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == "admin_list")
async def admin_list_callback(callback: types.CallbackQuery):
    """Обработчик кнопки 'Список личного состава'"""
    logger.info(f"📋 Запрос списка от пользователя {callback.from_user.id}")
    
    if not is_admin_check(callback.from_user.id):
        logger.warning(f"❌ Несанкционированный доступ к списку от {callback.from_user.id}")
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        logger.info("📊 Получаю список пользователей из БД...")
        users = await get_all_users()
        
        if not users:
            logger.info("📭 Список пользователей пуст")
            await callback.message.answer("📋 Список пуст.")
            await callback.answer()
            return
        
        logger.info(f"✅ Получено {len(users)} пользователей")
        
        output = "📋 <b>Список личного состава:</b>\n\n"
        
        for i, u in enumerate(users, 1):
            try:
                user_id = u.get('user_id', 'N/A')
                fio = u.get('fio', 'Не указано')
                rank = u.get('rank', 'Не указано')
                qual_rank = u.get('qual_rank', '')
                
                # Получаем статус с цветовой индикацией
                try:
                    status_text = get_user_status_with_colors(u)
                except Exception as e:
                    logger.error(f"Ошибка получения статуса для {fio}: {e}")
                    status_text = "⚠️ Ошибка статуса"
                
                output += f"{i}. 👤 {fio}\n"
                output += f"   Звание: {rank}\n"
                if qual_rank and qual_rank not in ['None', '']:
                    output += f"   Квалификация: {qual_rank}\n"
                output += f"   {status_text}\n"
                output += f"   /user{user_id}\n\n"
                
            except Exception as e:
                logger.error(f"Ошибка обработки пользователя {i}: {e}")
                continue
        
        # Разбиваем на сообщения если больше 4000 символов
        chunks = [output[i:i+4000] for i in range(0, len(output), 4000)]
        logger.info(f"📤 Отправляю {len(chunks)} сообщений со списком")
        
        for chunk in chunks:
            await callback.message.answer(chunk)
        
        await callback.answer()
        logger.info("✅ Список успешно отправлен")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при загрузке списка: {e}", exc_info=True)
        await callback.message.answer(f"❌ Ошибка при загрузке списка\n\nТехническая информация:\n{type(e).__name__}: {e}")
        await callback.answer()

@router.message(Command("list"))
async def admin_list_cmd(message: types.Message):
    """Команда /list для получения списка"""
    await cleanup_last_bot_message(message)
    
    if not is_admin_check(message.from_user.id):
        return
    
    try:
        users = await get_all_users()
        output = "📋 <b>Список личного состава:</b>\n\n"
        
        for i, u in enumerate(users, 1):
            user_id = u.get('user_id', 'N/A')
            fio = u.get('fio', 'Не указано')
            rank = u.get('rank', 'Не указано')
            qual_rank = u.get('qual_rank', '')
            status_text = get_user_status_with_colors(u)
            
            output += f"{i}. 👤 {fio}\n"
            output += f"   Звание: {rank}\n"
            if qual_rank and qual_rank not in ['None', '']:
                output += f"   Квалификация: {qual_rank}\n"
            output += f"   {status_text}\n"
            output += f"   /user{user_id}\n\n"
        
        chunks = [output[i:i+4000] for i in range(0, len(output), 4000)]
        for chunk in chunks:
            await message.answer(chunk)
            
    except Exception as e:
        logger.error(f"Ошибка в /list: {e}", exc_info=True)
        await send_and_save(message, f"❌ Ошибка при загрузке списка: {e}")

@router.message(F.text.startswith("/user"))
async def show_user_full_profile(message: types.Message):
    """Показывает полную анкету пользователя по команде /user{user_id}"""
    try:
        from database import get_user
        user_id = int(message.text.replace("/user", ""))
        logger.info(f"🔍 Запрос анкеты пользователя {user_id}")
        
        user = await get_user(user_id)
        
        if not user:
            await send_and_save(message, "❌ Пользователь не найден")
            return
        
        text = f"👤 <b>ПОЛНАЯ АНКЕТА</b>\n\n"
        text += f"📋 <b>Основные данные:</b>\n"
        text += f"• ФИО: {user.get('fio', 'Не указано')}\n"
        text += f"• Звание: {user.get('rank', 'Не указано')}\n"
        text += f"• Квалификация: {user.get('qual_rank', 'Не указано')}\n\n"
        
        text += f"📅 <b>Сроки и документы:</b>\n"
        text += f"• Отпуск: {user.get('vacation_start', 'Не указано')} - {user.get('vacation_end', 'Не указано')}\n"
        text += f"• ВЛК: {user.get('vlk_date', 'Не пройдено')}\n"
        text += f"• УМО: {user.get('umo_date', 'Не пройдено')}\n\n"
        
        text += f"✈️ <b>КБП:</b>\n"
        text += f"• КБП-4 МД-М: {user.get('kbp_4_md_m', 'Не пройдено')}\n"
        text += f"• КБП-7 МД-М: {user.get('kbp_7_md_m', 'Не пройдено')}\n"
        text += f"• КБП-4 МД-90А: {user.get('kbp_4_md_90a', 'Не пройдено')}\n"
        text += f"• КБП-7 МД-90А: {user.get('kbp_7_md_90a', 'Не пройдено')}\n\n"
        
        text += f"🪂 <b>Прыжки:</b>\n"
        text += f"• Дата: {user.get('jumps_date', 'Не указано')}\n\n"
        
        status_text = get_user_status_with_colors(user)
        text += f"\n{status_text}\n"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_list")]
        ])
        
        await send_and_save(message, text, reply_markup=kb)
        logger.info(f"✅ Анкета пользователя {user_id} отправлена")
        
    except Exception as e:
        logger.error(f"Ошибка показа анкеты: {e}", exc_info=True)
        await send_and_save(message, "❌ Ошибка при загрузке анкеты")
