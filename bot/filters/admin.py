"""
Фильтр для проверки администратора
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import config


class IsAdmin(BaseFilter):
    """Фильтр проверки администратора"""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        """Проверяем, является ли пользователь админом"""
        user_id = event.from_user.id if event.from_user else None
        return user_id in config.admin_ids
