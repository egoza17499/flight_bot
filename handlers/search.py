from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import search_info
from states import SearchInfo
from .common import cleanup_last_bot_message, send_and_save, is_admin_check, is_duplicate_result, save_search_result, get_persistent_menu
from utils import extract_airport_info

router = Router()

@router.message(F.text == "📚 Полезная информация")
async def start_search(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await state.set_state(SearchInfo.waiting_query)
    quick_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Чкаловский"), KeyboardButton(text="🔍 Стригино")],
            [KeyboardButton(text="🔍 Москва"), KeyboardButton(text="🔍 Санкт-Петербург")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    await send_and_save(
        message, 
        "🔍 Напишите город или аэродром, информация по которому вас интересует:",
        reply_markup=quick_kb
    )

@router.message(SearchInfo.waiting_query)
async def process_search(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    query = message.text.strip()
    
    if query.lower() == "отмена" or query == "❌ Отмена":
        await state.clear()
        admin = is_admin_check(message.from_user.id)
        await send_and_save(message, "❌ Поиск отменен", reply_markup=get_persistent_menu(is_admin=admin))
        return
    
    results = await search_info(query)
    
    if results:
        for result_text in results:
            if is_duplicate_result(message.chat.id, query, result_text):
                continue
            
            save_search_result(message.chat.id, query, result_text)
            
            header = f"🔍 <b>Вот что смог найти по запросу: {query}</b>\n\n"
            airport_info = extract_airport_info(query, result_text)
            if airport_info:
                header += airport_info + "\n\n"
            header += "<b>Полезные номера:</b>\n"
            
            full_text = header + result_text
            await message.answer(full_text)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать другой поиск", callback_data="new_search")]
        ])
        await send_and_save(message, "❌ Информация не найдена, извините.", reply_markup=kb)
    
    await state.clear()

@router.callback_query(F.data == "new_search")
async def new_search_callback(callback: types.CallbackQuery):
    await callback.message.answer(
        "🔍 Введите новый запрос:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Чкаловский"), KeyboardButton(text="🔍 Стригино")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    )
    await callback.answer()
