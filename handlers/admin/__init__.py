from aiogram import Router
from . import start, profile, search, list, manage, stats, test  # Добавили test

router = Router()

# Регистрируем роутеры
router.include_router(start.router)
router.include_router(profile.router)
router.include_router(search.router)
router.include_router(list.router)
router.include_router(manage.router)
router.include_router(stats.router)
router.include_router(test.router)  # Добавили тест

__all__ = ["router"]
