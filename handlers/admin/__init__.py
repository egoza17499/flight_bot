from aiogram import Router
from .list import router as list_router
from .stats import router as stats_router
from .airports import router as airports_router
from .manage import router as manage_router

# Создаем главный роутер для админки
router = Router()

# Подключаем все роутеры админки
router.include_router(list_router)
router.include_router(stats_router)
router.include_router(airports_router)
router.include_router(manage_router)
