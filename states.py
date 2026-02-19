from aiogram.fsm.state import State, StatesGroup

# ========== РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ ==========
class Registration(StatesGroup):
    """Состояния для прохождения регистрации пользователя"""
    fio = State()           # Ввод ФИО
    rank = State()          # Ввод воинского звания
    qual_rank = State()     # Ввод квалификационного разряда
    vacation = State()      # Ввод дат отпуска
    vlk = State()           # Ввод даты ВЛК
    umo = State()           # Ввод даты УМО
    kbp_4_md_m = State()    # Ввод КБП-4 Ил-76 МД-М
    kbp_7_md_m = State()    # Ввод КБП-7 Ил-76 МД-М
    kbp_4_md_90a = State()  # Ввод КБП-4 Ил-76 МД-90А
    kbp_7_md_90a = State()  # Ввод КБП-7 Ил-76 МД-90А
    jumps = State()         # Ввод даты прыжков с ПДС

# ========== РЕДАКТИРОВАНИЕ ПРОФИЛЯ ==========
class EditProfile(StatesGroup):
    """Состояния для редактирования профиля пользователя"""
    entering_value = State()  # Ввод нового значения поля

# ========== ПОИСК ИНФОРМАЦИИ ==========
class SearchInfo(StatesGroup):
    """Состояния для поиска информации по аэродромам"""
    waiting_query = State()  # Ожидание поискового запроса

# ========== АДМИН ПАНЕЛЬ ==========
class AdminStates(StatesGroup):
    """Состояния для административных функций"""
    adding_info = State()      # Добавление информации в базу
    deleting_info = State()    # Удаление информации из базы
    adding_admin = State()     # Добавление нового админа
    removing_admin = State()   # Удаление админа
    searching_user = State()   # Поиск пользователя по фамилии

# ========== ДОПОЛНИТЕЛЬНЫЕ СОСТОЯНИЯ ==========
class Confirmation(StatesGroup):
    """Состояния для подтверждения действий"""
    waiting_confirm = State()  # Ожидание подтверждения (да/нет)

class Form(StatesGroup):
    """Общие состояния для форм"""
    input_text = State()       # Ввод текста
    input_number = State()     # Ввод числа
    input_date = State()       # Ввод даты
