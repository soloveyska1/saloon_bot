"""
Keyboards package - клавиатуры бота
"""

from bot.keyboards.reply import get_main_menu
from bot.keyboards.inline import get_main_menu_kb, get_cancel_kb, get_back_kb

__all__ = [
    "get_main_menu",
    "get_main_menu_kb",
    "get_cancel_kb",
    "get_back_kb",
]
