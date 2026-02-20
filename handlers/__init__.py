from aiogram import Router
from .start import router as start_router
from .profile import router as profile_router
from .search import router as search_router
from .callbacks import router as callbacks_router
from .text_handler import router as text_router
from .admin import router as admin_router

# Создаем главный роутер
router = Router()

# Подключаем все роутеры
router.include_router(start_router)
router.include_router(profile_router)
router.include_router(search_router)
router.include_router(callbacks_router)
router.include_router(admin_router)  # ✅ Подключаем весь admin одним роутером
router.include_router(text_router)  # Последний!
