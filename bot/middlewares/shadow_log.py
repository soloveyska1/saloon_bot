"""
Shadow Log Middleware
Автоматическое архивирование файлов в лог-канал
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message

from database.models import User
from services.logger_service import LOG_CHANNEL_ID

logger = logging.getLogger(__name__)


class ShadowLogMiddleware(BaseMiddleware):
    """
    Middleware для автоматического архивирования файлов

    При получении файла (document/photo) от пользователя:
    - Пересылает файл в лог-канал
    - Добавляет информацию о пользователе
    - Помечает тегом #archive

    Используется для:
    - Резервного копирования всех файлов
    - Мониторинга контента
    - Аудита
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Проверяем, что это сообщение
        if isinstance(event, Message):
            message: Message = event
            bot: Bot = data.get("bot")
            user: User | None = data.get("user")

            # Проверяем наличие файлов
            if message.document or message.photo:
                await self._archive_file(bot, message, user)

        # Продолжаем обработку
        return await handler(event, data)

    async def _archive_file(
        self,
        bot: Bot,
        message: Message,
        user: User | None,
    ) -> None:
        """Архивирует файл в лог-канал"""
        try:
            # Формируем информацию о пользователе
            if user:
                user_info = f'👤 <a href="tg://user?id={user.telegram_id}">{user.first_name}</a>\n'
                user_info += f"🆔 <code>{user.telegram_id}</code>\n"
                if user.username:
                    user_info += f"📛 @{user.username}\n"
            else:
                tg_user = message.from_user
                user_info = f"👤 {tg_user.first_name}\n"
                user_info += f"🆔 <code>{tg_user.id}</code>\n"

            # Определяем тип и информацию о файле
            if message.document:
                file_type = "📄 Документ"
                file_name = message.document.file_name or "Без имени"
                file_size = message.document.file_size
                file_id = message.document.file_id

                file_info = f"<b>{file_type}</b>\n"
                file_info += f"📁 <code>{file_name}</code>\n"
                file_info += f"📊 Размер: {self._format_size(file_size)}\n"

            elif message.photo:
                file_type = "🖼 Фото"
                # Берём самое большое фото
                photo = message.photo[-1]
                file_id = photo.file_id

                file_info = f"<b>{file_type}</b>\n"
                file_info += f"📐 {photo.width}x{photo.height}\n"

            else:
                return

            # Формируем caption для архива
            caption = f"📎 <b>АРХИВ ФАЙЛА</b>\n"
            caption += "➖➖➖➖➖➖➖➖➖➖\n"
            caption += user_info
            caption += "➖➖➖➖➖➖➖➖➖➖\n"
            caption += file_info
            caption += "\n#archive #file"

            # Пересылаем файл в канал
            if message.document:
                await bot.send_document(
                    chat_id=LOG_CHANNEL_ID,
                    document=file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
            elif message.photo:
                await bot.send_photo(
                    chat_id=LOG_CHANNEL_ID,
                    photo=file_id,
                    caption=caption,
                    parse_mode="HTML",
                )

            logger.debug(f"Файл от {message.from_user.id} заархивирован в лог-канал")

        except Exception as e:
            logger.error(f"Ошибка архивирования файла: {e}")

    @staticmethod
    def _format_size(size_bytes: int | None) -> str:
        """Форматирует размер файла"""
        if not size_bytes:
            return "Неизвестно"

        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
