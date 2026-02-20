@router.message(F.text.startswith("/user"))
async def show_user_full_profile(message: types.Message):
    """Показывает полную анкету пользователя по команде /user{user_id}"""
    try:
        from database import get_user
        # Извлекаем user_id из команды /user123456789
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
        
        # Добавляем статус с цветовой индикацией
        status_text = get_user_status_with_colors(user)
        if status_text:
            text += f"\n{status_text}\n"
        
        # Кнопка назад
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_list")]
        ])
        
        await send_and_save(message, text, reply_markup=kb)
        logger.info(f"✅ Анкета пользователя {user_id} отправлена")
        
    except Exception as e:
        logger.error(f"Ошибка показа анкеты: {e}", exc_info=True)
        await send_and_save(message, "❌ Ошибка при загрузке анкеты")
