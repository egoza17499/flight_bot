from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    fio = State()
    rank = State()
    qual_rank = State()
    vacation = State()
    vlk = State()
    umo = State()
    kbp_4_md_m = State()
    kbp_7_md_m = State()
    kbp_4_md_90a = State()
    kbp_7_md_90a = State()
    jumps = State()

class EditProfile(StatesGroup):
    entering_value = State()

class SearchInfo(StatesGroup):
    waiting_query = State()

class AdminStates(StatesGroup):
    searching = State()
    adding_info = State()
    deleting_info = State()
