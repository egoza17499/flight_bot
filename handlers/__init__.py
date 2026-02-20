from aiogram import Router, F, types
from aiogram.filters import Command
from . import start, profile, search, admin, common
from .common import cleanup_last_bot_message, send_and_save, is_admin_check

router = Router()

# Подключаем модули
router.include_router(start.router)
router.include_router(profile.router)
router.include_router(search.router)
router.include_router(admin.router)

# Команды помощи и отмены
@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await state.clear()
    admin = is_admin_check(message.from_user.id)
    await send_and_save(
        message,
        "❌ Отменено",
        reply_markup=get_main_menu(is_admin=admin)
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await cleanup_last_bot_message(message)
    text = "ℹ️ <b>Помощь:</b>\n\n"
    text += "/start - Начать\n"
    text += "/help - Помощь\n"
    text += "/cancel - Отмена\n"
    text += "/test_airports - Тест базы\n"
    if is_admin_check(message.from_user.id):
        text += "\n🛡 <b>Админ:</b>\n"
        text += "/list - Список\n"
        text += "/admin_menu - Меню\n"
        text += "/fill_airports - База"
    await send_and_save(message, text)

@router.message(Command("admin_menu"))
async def admin_menu_cmd(message: types.Message):
    await cleanup_last_bot_message(message)
    if not is_admin_check(message.from_user.id):
        return
    await send_and_save(message, "🛡 <b>Панель админа</b>", reply_markup=get_admin_menu())

__all__ = ["router"]
