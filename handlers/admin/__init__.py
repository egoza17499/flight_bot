from aiogram import Router
from . import list, stats, airports, manage, test

router = Router()

router.include_router(list.router)
router.include_router(stats.router)
router.include_router(airports.router)
router.include_router(manage.router)
router.include_router(test.router)

__all__ = ["router"]
