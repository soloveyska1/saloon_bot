"""
Inline клавиатуры (кнопки под сообщениями)
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню салуна (под приветственным фото)"""
    builder = InlineKeyboardBuilder()

    # Ряд 1: Главная кнопка заказа
    builder.row(
        InlineKeyboardButton(text="🎯 Заказать работу", callback_data="order_work")
    )

    # Ряд 2: Профиль и цены
    builder.row(
        InlineKeyboardButton(text="🤠 Моё досье", callback_data="profile"),
        InlineKeyboardButton(text="💰 Цены", callback_data="prices"),
    )

    # Ряд 3: Правила и поддержка
    builder.row(
        InlineKeyboardButton(text="📜 Кодекс Салуна", callback_data="rules"),
        InlineKeyboardButton(text="🆘 Позвать Шефа", callback_data="support"),
    )

    return builder.as_markup()


def get_cancel_kb() -> InlineKeyboardMarkup:
    """Кнопка отмены действия"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_back_kb(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    """Кнопка возврата в меню"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data=callback_data)
    )
    return builder.as_markup()
