"""
User handlers - хендлеры для обычных пользователей
"""

from aiogram import Router

from bot.handlers.user.start import router as start_router
from bot.handlers.user.menu import router as menu_router
from bot.handlers.user.profile import router as profile_router
from bot.handlers.user.rules import router as rules_router
from bot.handlers.user.order import router as order_router

router = Router(name="user")

# Подключаем все пользовательские хендлеры
router.include_router(start_router)
router.include_router(menu_router)
router.include_router(profile_router)
router.include_router(rules_router)
router.include_router(order_router)
