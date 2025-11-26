"""
Logger Service - Логирование событий в Telegram канал
Enterprise CRM Logging System
"""

import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot

# ID канала для логирования
LOG_CHANNEL_ID = -1003300275622

logger = logging.getLogger(__name__)


# Эмодзи для типов событий
EVENT_EMOJIS = {
    "new_user": "🟢",
    "new_order": "📝",
    "order_status": "📋",
    "payment": "💸",
    "refund": "↩️",
    "deposit": "💵",
    "bonus": "🎁",
    "error": "🚨",
    "warning": "⚠️",
    "info": "ℹ️",
    "admin": "👨‍💼",
    "file": "📎",
    "terms": "📜",
    "referral": "🔗",
}

# Названия событий на русском
EVENT_NAMES = {
    "new_user": "Новый пользователь",
    "new_order": "Новый заказ",
    "order_status": "Статус заказа",
    "payment": "Оплата",
    "refund": "Возврат",
    "deposit": "Пополнение",
    "bonus": "Начисление бонуса",
    "error": "Ошибка",
    "warning": "Предупреждение",
    "info": "Информация",
    "admin": "Действие админа",
    "file": "Файл загружен",
    "terms": "Оферта принята",
    "referral": "Реферал",
}


def format_user_link(telegram_id: int, name: str = "Пользователь") -> str:
    """
    Создаёт кликабельную ссылку на пользователя
    Magic Link формат для Telegram
    """
    return f'<a href="tg://user?id={telegram_id}">{name}</a>'


def format_user_command(telegram_id: int) -> str:
    """
    Создаёт команду для быстрого поиска пользователя
    Формат: /user_12345
    """
    return f"/user_{telegram_id}"


async def log_to_channel(
    bot: Bot,
    event_type: str,
    message: str,
    tags: Optional[list[str]] = None,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    order_id: Optional[int] = None,
    extra_data: Optional[dict] = None,
) -> bool:
    """
    Отправляет форматированный лог в канал

    Args:
        bot: Экземпляр бота
        event_type: Тип события (new_user, new_order, payment, error и т.д.)
        message: Основной текст сообщения
        tags: Список тегов для фильтрации (#order, #payment и т.д.)
        user_id: Telegram ID пользователя (для Magic Link)
        user_name: Имя пользователя для отображения
        order_id: ID заказа (если применимо)
        extra_data: Дополнительные данные для отображения

    Returns:
        bool: True если успешно отправлено
    """
    try:
        # Получаем эмодзи и название события
        emoji = EVENT_EMOJIS.get(event_type, "📌")
        event_name = EVENT_NAMES.get(event_type, event_type.upper())

        # Формируем заголовок
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        header = f"{emoji} <b>{event_name}</b>\n"
        header += f"<code>{timestamp}</code>\n"
        header += "➖➖➖➖➖➖➖➖➖➖\n"

        # Добавляем информацию о пользователе с Magic Link
        user_info = ""
        if user_id:
            display_name = user_name or "Пользователь"
            user_link = format_user_link(user_id, display_name)
            user_cmd = format_user_command(user_id)
            user_info = f"👤 {user_link}\n"
            user_info += f"🆔 <code>{user_id}</code> | {user_cmd}\n"

        # Добавляем информацию о заказе
        order_info = ""
        if order_id:
            order_info = f"📦 Заказ: <code>#{order_id}</code>\n"

        # Основное сообщение
        body = f"\n{message}\n"

        # Дополнительные данные
        extra_info = ""
        if extra_data:
            extra_info = "\n<i>Доп. данные:</i>\n"
            for key, value in extra_data.items():
                extra_info += f"• {key}: <code>{value}</code>\n"

        # Теги
        tags_str = ""
        if tags:
            tags_str = "\n" + " ".join([f"#{tag}" for tag in tags])

        # Собираем полное сообщение
        full_message = header + user_info + order_info + body + extra_info + tags_str

        # Отправляем в канал
        await bot.send_message(
            chat_id=LOG_CHANNEL_ID,
            text=full_message,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        return True

    except Exception as e:
        logger.error(f"Ошибка отправки лога в канал: {e}")
        return False


async def log_new_user(
    bot: Bot,
    telegram_id: int,
    username: Optional[str],
    first_name: str,
    referrer_id: Optional[int] = None,
) -> bool:
    """Логирование регистрации нового пользователя"""

    message = f"<b>{first_name}</b>"
    if username:
        message += f" (@{username})"
    message += " присоединился к Салуну!"

    tags = ["user", "registration"]
    extra_data = {}

    if referrer_id:
        message += f"\n🔗 Приглашён пользователем {format_user_command(referrer_id)}"
        tags.append("referral")
        extra_data["referrer_id"] = referrer_id

    return await log_to_channel(
        bot=bot,
        event_type="new_user",
        message=message,
        tags=tags,
        user_id=telegram_id,
        user_name=first_name,
        extra_data=extra_data if extra_data else None,
    )


async def log_new_order(
    bot: Bot,
    order_id: int,
    user_id: int,
    user_name: str,
    work_type: str,
    subject: str,
) -> bool:
    """Логирование нового заказа"""

    # Обрезаем тему если слишком длинная
    subject_short = subject[:100] + "..." if len(subject) > 100 else subject

    message = f"📝 <b>Тип:</b> {work_type}\n"
    message += f"📚 <b>Тема:</b> {subject_short}"

    return await log_to_channel(
        bot=bot,
        event_type="new_order",
        message=message,
        tags=["order", "new"],
        user_id=user_id,
        user_name=user_name,
        order_id=order_id,
    )


async def log_payment(
    bot: Bot,
    user_id: int,
    user_name: str,
    amount: int,
    order_id: Optional[int] = None,
    transaction_type: str = "payment",
) -> bool:
    """Логирование платежа/транзакции"""

    # Определяем тип события
    if transaction_type == "deposit":
        event_type = "deposit"
        message = f"💵 Пополнение баланса: <b>+{amount} ₽</b>"
    elif transaction_type == "refund":
        event_type = "refund"
        message = f"↩️ Возврат средств: <b>+{amount} ₽</b>"
    elif transaction_type == "bonus":
        event_type = "bonus"
        message = f"🎁 Начислен бонус: <b>+{amount} ₽</b>"
    else:
        event_type = "payment"
        message = f"💸 Оплата: <b>-{abs(amount)} ₽</b>"

    return await log_to_channel(
        bot=bot,
        event_type=event_type,
        message=message,
        tags=["money", transaction_type],
        user_id=user_id,
        user_name=user_name,
        order_id=order_id,
        extra_data={"amount": f"{amount} ₽"},
    )


async def log_order_status(
    bot: Bot,
    order_id: int,
    user_id: int,
    user_name: str,
    old_status: str,
    new_status: str,
) -> bool:
    """Логирование изменения статуса заказа"""

    message = f"📋 Статус изменён:\n"
    message += f"<code>{old_status}</code> → <code>{new_status}</code>"

    return await log_to_channel(
        bot=bot,
        event_type="order_status",
        message=message,
        tags=["order", "status", new_status],
        user_id=user_id,
        user_name=user_name,
        order_id=order_id,
    )


async def log_error(
    bot: Bot,
    error_message: str,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    extra_data: Optional[dict] = None,
) -> bool:
    """Логирование ошибки"""

    return await log_to_channel(
        bot=bot,
        event_type="error",
        message=f"<code>{error_message}</code>",
        tags=["error", "alert"],
        user_id=user_id,
        user_name=user_name,
        extra_data=extra_data,
    )


async def log_file_received(
    bot: Bot,
    user_id: int,
    user_name: str,
    file_type: str,
    file_name: Optional[str] = None,
) -> bool:
    """Логирование получения файла"""

    message = f"📎 Получен файл: <b>{file_type}</b>"
    if file_name:
        message += f"\n📄 Имя: <code>{file_name}</code>"

    return await log_to_channel(
        bot=bot,
        event_type="file",
        message=message,
        tags=["file", "archive"],
        user_id=user_id,
        user_name=user_name,
    )


async def log_terms_accepted(
    bot: Bot,
    user_id: int,
    user_name: str,
) -> bool:
    """Логирование принятия оферты"""

    return await log_to_channel(
        bot=bot,
        event_type="terms",
        message="Пользователь принял условия оферты",
        tags=["terms", "legal"],
        user_id=user_id,
        user_name=user_name,
    )
