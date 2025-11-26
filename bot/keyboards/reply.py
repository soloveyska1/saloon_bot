"""
Reply клавиатуры (обычные кнопки)
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню салуна"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Новый заказ"),
                KeyboardButton(text="📋 Мои заказы"),
            ],
            [
                KeyboardButton(text="👤 Личный кабинет"),
                KeyboardButton(text="💰 Бонусы"),
            ],
            [
                KeyboardButton(text="📞 Связаться с нами"),
                KeyboardButton(text="❓ Помощь"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие, ковбой...",
    )
    return keyboard
