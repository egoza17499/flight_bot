from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    fio = State()
    rank = State()
    qual_rank = State()
    vacation = State() # Вводим сразу диапазон
    vlk = State()
    umo = State() # Опционально
    kbp_4_md_m = State()
    kbp_7_md_m = State()
    kbp_4_md_90a = State()
    kbp_7_md_90a = State()
    jumps = State()

class EditProfile(StatesGroup):
    choosing_field = State()
    entering_value = State()

class SearchInfo(StatesGroup):
    waiting_query = State()