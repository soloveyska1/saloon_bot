"""
Middleware для работы с базой данных
Автоматическая регистрация пользователей
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import async_session
from database.models import User


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для инъекции сессии БД в хендлеры
    и автоматической регистрации новых пользователей
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            # Добавляем сессию в data для использования в хендлерах
            data["session"] = session

            # Получаем пользователя Telegram
            tg_user: TgUser | None = data.get("event_from_user")

            if tg_user and not tg_user.is_bot:
                # Ищем или создаём пользователя в БД
                user = await self._get_or_create_user(session, tg_user)
                data["user"] = user

            result = await handler(event, data)

            # Сохраняем изменения
            await session.commit()

            return result

    async def _get_or_create_user(
        self, session: AsyncSession, tg_user: TgUser
    ) -> User:
        """Получить пользователя из БД или создать нового"""

        # Ищем существующего пользователя
        stmt = select(User).where(User.telegram_id == tg_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Обновляем данные пользователя (имя/username могли измениться)
            user.username = tg_user.username
            user.first_name = tg_user.first_name
            user.last_name = tg_user.last_name
            return user

        # Создаём нового ковбоя
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name or None,
            rank="greenhorn",  # Новичок
        )
        session.add(user)
        await session.flush()  # Получаем ID сразу

        return user
