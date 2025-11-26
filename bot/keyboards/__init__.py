"""
Keyboards package - клавиатуры бота
"""

from bot.keyboards.reply import get_main_menu
from bot.keyboards.inline import (
    # Главное меню
    get_main_menu_kb,
    # Навигация
    get_cancel_kb,
    get_back_kb,
    # Воронка заказа
    get_work_types_kb,
    get_deadline_kb,
    get_skip_kb,
    get_files_done_kb,
    get_order_summary_kb,
    get_confirm_order_kb,
    # Оплата
    get_payment_kb,
    # Админ-панель
    get_admin_menu_kb,
    get_admin_orders_kb,
    get_admin_order_kb,
    get_admin_back_kb,
    get_admin_cancel_kb,
    # Константы
    WORK_TYPES,
    DEADLINES,
)

__all__ = [
    "get_main_menu",
    "get_main_menu_kb",
    "get_cancel_kb",
    "get_back_kb",
    "get_work_types_kb",
    "get_deadline_kb",
    "get_skip_kb",
    "get_files_done_kb",
    "get_order_summary_kb",
    "get_confirm_order_kb",
    "get_payment_kb",
    "get_admin_menu_kb",
    "get_admin_orders_kb",
    "get_admin_order_kb",
    "get_admin_back_kb",
    "get_admin_cancel_kb",
    "WORK_TYPES",
    "DEADLINES",
]
