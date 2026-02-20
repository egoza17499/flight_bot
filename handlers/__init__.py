from aiogram import Router
from .start import router as start_router
from .profile import router as profile_router
from .search import router as search_router
from .callbacks import router as callbacks_router
from .text_handler import router as text_router
from .admin.list import router as admin_list_router
from .admin.stats import router as admin_stats_router
from .admin.airports import router as admin_airports_router
from .admin.manage import router as admin_manage_router

# Создаем главный роутер
router = Router()

# Подключаем все роутеры
router.include_router(start_router)
router.include_router(profile_router)
router.include_router(search_router)
router.include_router(callbacks_router)
router.include_router(admin_list_router)
router.include_router(admin_stats_router)
router.include_router(admin_airports_router)
router.include_router(admin_manage_router)
router.include_router(text_router)  # Последний!
