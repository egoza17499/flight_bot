from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from states import SearchInfo
from database import search_info
from .common import cleanup_last_bot_message, send_and_save

router = Router()

@router.message(F.text == "📚 Полезная информация")
async def start_search(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    await state.set_state(SearchInfo.waiting_query)
    await send_and_save(message, "🔍 Напишите город или аэродром, информация по которому вас интересует:")

@router.message(SearchInfo.waiting_query)
async def process_search(message: types.Message, state: FSMContext):
    await cleanup_last_bot_message(message)
    results = await search_info(message.text)
    if results:
        for res in results:
            await message.answer(res)
    else:
        await send_and_save(message, "❌ Информация не найдена, извините.")
    await state.clear()
