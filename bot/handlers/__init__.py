"""
Handlers package - обработчики сообщений и callback'ов
"""

from aiogram import Router

from bot.handlers.user import router as user_router
from bot.handlers.admin import router as admin_router


def setup_routers() -> Router:
    """Настройка и объединение всех роутеров"""
    router = Router()

    # Подключаем роутеры
    router.include_router(user_router)
    router.include_router(admin_router)

    return router
