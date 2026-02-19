from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu(is_admin=False):
    """Главное меню бота"""
    kb = [
        [KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="📚 Полезная информация")]
    ]
    
    # Кнопка админа добавляется только для администратора
    if is_admin:
        kb.append([KeyboardButton(text="🛡 Функции админа")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_edit_menu():
    """Меню редактирования профиля"""
    kb = [
        [InlineKeyboardButton(text="ФИО", callback_data="edit_fio")],
        [InlineKeyboardButton(text="Звание", callback_data="edit_rank")],
        [InlineKeyboardButton(text="Квалификация", callback_data="edit_qual_rank")],
        [InlineKeyboardButton(text="Отпуск (даты)", callback_data="edit_vacation")],
        [InlineKeyboardButton(text="ВЛК", callback_data="edit_vlk_date")],
        [InlineKeyboardButton(text="УМО", callback_data="edit_umo_date")],
        [InlineKeyboardButton(text="КБП-4 МД-М", callback_data="edit_kbp_4_md_m")],
        [InlineKeyboardButton(text="КБП-7 МД-М", callback_data="edit_kbp_7_md_m")],
        [InlineKeyboardButton(text="КБП-4 МД-90А", callback_data="edit_kbp_4_md_90a")],
        [InlineKeyboardButton(text="КБП-7 МД-90А", callback_data="edit_kbp_7_md_90a")],
        [InlineKeyboardButton(text="Прыжки", callback_data="edit_jumps_date")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_admin_menu():
    """Меню администратора"""
    kb = [
        [InlineKeyboardButton(text="📋 Список личного состава", callback_data="admin_list")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="✈️ Заполнить базу аэродромов", callback_data="admin_fill_airports")],
        [InlineKeyboardButton(text="🔍 Поиск по фамилии", callback_data="admin_search")],
        [InlineKeyboardButton(text="📝 Добавить информацию", callback_data="admin_add_info")],
        [InlineKeyboardButton(text="🗑 Удалить информацию", callback_data="admin_del_info")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Маппинг callback_data на поля в базе данных
FIELD_MAP = {
    "fio": "fio",
    "rank": "rank",
    "qual_rank": "qual_rank",
    "vacation": "vacation",
    "vlk_date": "vlk_date",
    "umo_date": "umo_date",
    "kbp_4_md_m": "kbp_4_md_m",
    "kbp_7_md_m": "kbp_7_md_m",
    "kbp_4_md_90a": "kbp_4_md_90a",
    "kbp_7_md_90a": "kbp_7_md_90a",
    "jumps_date": "jumps_date"
}

# Человеко-читаемые названия полей
FIELD_NAMES = {
    "fio": "ФИО",
    "rank": "Звание",
    "qual_rank": "Квалификационный разряд",
    "vacation": "Отпуск (формат: ДД.ММ.ГГГГ - ДД.ММ.ГГГГ)",
    "vlk_date": "ВЛК (формат: ДД.ММ.ГГГГ)",
    "umo_date": "УМО (формат: ДД.ММ.ГГГГ или 'нет')",
    "kbp_4_md_m": "КБП-4 Ил-76 МД-М (формат: ДД.ММ.ГГГГ)",
    "kbp_7_md_m": "КБП-7 Ил-76 МД-М (формат: ДД.ММ.ГГГГ)",
    "kbp_4_md_90a": "КБП-4 Ил-76 МД-90А (формат: ДД.ММ.ГГГГ)",
    "kbp_7_md_90a": "КБП-7 Ил-76 МД-90А (формат: ДД.ММ.ГГГГ)",
    "jumps_date": "Прыжки (формат: ДД.ММ.ГГГГ или 'освобожден')"
}
