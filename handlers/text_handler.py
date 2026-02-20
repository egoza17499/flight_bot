from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from .common import cleanup_last_bot_message, send_and_save, is_admin_check, get_persistent_menu
from database import get_user

router = Router()

@router.message(F.text)
async def handle_any_text(message: types.Message, state: FSMContext):
    """Любое текстовое сообщение = возврат в меню, но только если нет активного состояния"""
    
    # Игнорируем команды /user... (просмотр анкеты)
    if message.text.startswith("/user"):
        return  # Пропускаем, пусть обрабатывается другим хендлером
    
    # Проверяем текущее состояние
    current_state = await state.get_state()
    
    # Если есть активное состояние — пропускаем
    if current_state is not None:
        return
    
    # Игнорируем ответы на сообщения бота
    if message.reply_to_message and message.reply_to_message.from_user.id == message.bot.id:
        return
    
    await cleanup_last_bot_message(message)
    
    user = await get_user(message.from_user.id)
    admin = is_admin_check(message.from_user.id)
    
    if user and user.get('registered'):
        await send_and_save(
            message,
            "Добро пожаловать обратно! Выберите действие:",
            reply_markup=get_persistent_menu(is_admin=admin)
        )
    else:
        await send_and_save(
            message,
            "👋 Приветствую! Для доступа к функциям необходимо пройти регистрацию.",
            reply_markup=get_persistent_menu(is_admin=admin)
        )
