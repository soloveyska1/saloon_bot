"""
User handlers - хендлеры для обычных пользователей
"""

from aiogram import Router

from bot.handlers.user.start import router as start_router

router = Router(name="user")

# Подключаем все пользовательские хендлеры
router.include_router(start_router)
