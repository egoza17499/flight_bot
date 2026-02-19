from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    kb = [
        [KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="📚 Полезная информация")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_edit_menu():
    fields = [
        ["ФИО"], ["Звание"], ["Квалификация"],
        ["Отпуск (даты)"], ["ВЛК"], ["УМО"],
        ["КБП-4 МД-М"], ["КБП-7 МД-М"],
        ["КБП-4 МД-90А"], ["КБП-7 МД-90А"],
        ["Прыжки"]
    ]
    # Превращаем в кнопки
    kb = [[InlineKeyboardButton(text=f[0], callback_data=f"edit_{f[0].lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')}")] for f in fields]
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Маппинг кнопок на поля БД
FIELD_MAP = {
    "fio": "fio", "звание": "rank", "квалификация": "qual_rank",
    "отпуск_даты": "vacation", "влк": "vlk_date", "умо": "umo_date",
    "кбп_4_мд_м": "kbp_4_md_m", "кбп_7_мд_м": "kbp_7_md_m",
    "кбп_4_мд_90а": "kbp_4_md_90a", "кбп_7_мд_90а": "kbp_7_md_90a",
    "прыжки": "jumps_date"
}