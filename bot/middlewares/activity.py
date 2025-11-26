"""
Activity Tracking Middleware
Отслеживание активности пользователей для CRM
"""

from datetime import datetime
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.models import User


class TrackActivityMiddleware(BaseMiddleware):
    """
    Middleware для отслеживания активности пользователей

    Обновляет поле last_active при каждом сообщении/callback от пользователя.
    Используется для:
    - Retention метрик
    - Сегментации пользователей
    - Определения "спящих" пользователей
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем пользователя из data (установлен DatabaseMiddleware)
        user: User | None = data.get("user")

        if user:
            # Обновляем время последней активности
            user.last_active = datetime.now()

        # Продолжаем обработку
        return await handler(event, data)
