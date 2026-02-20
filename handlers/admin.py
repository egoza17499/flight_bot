from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import get_all_users, get_all_admins, add_admin, remove_admin
from keyboards import get_admin_menu, get_admin_manage_menu
from config import ADMIN_ID

router = Router()

def is_admin_check(user_id):
    return user_id == ADMIN_ID

@router.message(F.text == "🛡 Функции админа")
async def admin_menu_button(message: types.Message):
    if not is_admin_check(message.from_user.id):
        await message.answer("❌ Доступ запрещен.")
        return
    await message.answer("🛡 <b>Панель администратора</b>\n\nВыберите действие:", reply_markup=get_admin_menu())

@router.callback_query(F.data == "admin_list")
async def admin_list_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    users = await get_all_users()
    output = "📋 <b>Список личного состава:</b>\n\n"
    for u in users:
        output += f"👤 {u['fio']} ({u['rank']})\n"
    await callback.message.answer(output[:4000])
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    users = await get_all_users()
    total = len(users)
    await callback.message.answer(f"📊 <b>Статистика:</b>\n\n👥 Всего пользователей: {total}")
    await callback.answer()

@router.callback_query(F.data == "admin_manage")
async def admin_manage_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    await callback.message.edit_text("👥 <b>Управление администраторами</b>\n\nВыберите действие:", reply_markup=get_admin_manage_menu())
    await callback.answer()

@router.callback_query(F.data == "admin_add")
async def admin_add_callback(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin_check(callback.from_user.id):
        return
    from states import AdminStates
    await state.set_state(AdminStates.adding_admin)
    await callback.message.answer("➕ Введите <b>User ID</b> для добавления в админы:")
    await callback.answer()

@router.callback_query(F.data == "admin_remove")
async def admin_remove_callback(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin_check(callback.from_user.id):
        return
    from states import AdminStates
    await state.set_state(AdminStates.removing_admin)
    await callback.message.answer("➖ Введите <b>User ID</b> для удаления из админов:")
    await callback.answer()

@router.callback_query(F.data == "admin_list_all")
async def admin_list_all_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    admins = await get_all_admins()
    text = "🛡 <b>Список администраторов:</b>\n\n"
    for i, admin in enumerate(admins, 1):
        badge = "👑" if admin['user_id'] == ADMIN_ID else "🛡"
        text += f"{i}. {badge} <code>{admin['user_id']}</code>\n"
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "admin_menu_back")
async def admin_menu_back_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    await callback.message.edit_text("🛡 <b>Панель администратора</b>\n\nВыберите действие:", reply_markup=get_admin_menu())
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: types.CallbackQuery):
    if not is_admin_check(callback.from_user.id):
        return
    from keyboards import get_main_menu
    await callback.message.answer("Выберите действие:", reply_markup=get_main_menu(is_admin=True))
    await callback.answer()

@router.message(AdminStates.adding_admin)
async def admin_add_process(message: types.Message):
    if not is_admin_check(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
        success, msg = await add_admin(target_id, message.from_user.id)
        await message.answer(msg)
    except:
        await message.answer("❌ Неверный формат! Введите числовой ID.")

@router.message(AdminStates.removing_admin)
async def admin_remove_process(message: types.Message):
    if not is_admin_check(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
        success, msg = await remove_admin(target_id, message.from_user.id)
        await message.answer(msg)
    except:
        await message.answer("❌ Неверный формат! Введите числовой ID.")
