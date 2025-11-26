"""
Inline клавиатуры (кнопки под сообщениями)
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены действия"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()
