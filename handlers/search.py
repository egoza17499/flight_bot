from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import search_info
from states import SearchInfo

router = Router()

@router.message(F.text == "📚 Полезная информация")
async def start_search(message: types.Message, state: FSMContext):
    await state.set_state(SearchInfo.waiting_query)
    await message.answer("🔍 Напишите город или аэродром, информация по которому вас интересует:")

@router.message(SearchInfo.waiting_query)
async def process_search(message: types.Message, state: FSMContext):
    results = await search_info(message.text)
    if results:
        for res in results:
            await message.answer(res)
    else:
        await message.answer("❌ Информация не найдена, извините.")
    await state.clear()
