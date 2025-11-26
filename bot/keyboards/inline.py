"""
Inline клавиатуры (кнопки под сообщениями)
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =============================================================================
# ГЛАВНОЕ МЕНЮ
# =============================================================================

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


# =============================================================================
# НАВИГАЦИЯ
# =============================================================================

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


# =============================================================================
# ВОРОНКА ЗАКАЗА
# =============================================================================

# Типы работ с callback_data
WORK_TYPES = {
    "type_coursework": "📚 Курсовая работа",
    "type_diploma": "🎓 Дипломная работа",
    "type_essay": "📝 Реферат",
    "type_practice": "📋 Отчёт по практике",
    "type_control": "✍️ Контрольная работа",
    "type_other": "📦 Другое",
}

# Сроки выполнения
DEADLINES = {
    "deadline_week": ("🟢 Не горит (7+ дней)", "week"),
    "deadline_medium": ("🟡 Поджимает (3-5 дней)", "medium"),
    "deadline_urgent": ("🔴 ПОЖАР! (1-2 дня)", "urgent"),
}


def get_work_types_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа работы"""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки типов работ (по 2 в ряд)
    for callback_data, text in WORK_TYPES.items():
        builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))

    # Располагаем по 2 кнопки в ряд
    builder.adjust(2)

    # Добавляем кнопку отмены отдельным рядом
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_order")
    )

    return builder.as_markup()


def get_deadline_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора дедлайна"""
    builder = InlineKeyboardBuilder()

    for callback_data, (text, _) in DEADLINES.items():
        builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))

    # Кнопка отмены
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_order")
    )

    return builder.as_markup()


def get_skip_kb(skip_callback: str = "skip") -> InlineKeyboardMarkup:
    """Кнопка 'Пропустить' (для необязательных полей)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить", callback_data=skip_callback),
        InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_order"),
    )
    return builder.as_markup()


def get_files_done_kb() -> InlineKeyboardMarkup:
    """Клавиатура после загрузки файлов"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Всё загрузил, готово!", callback_data="files_done")
    )
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить (без файлов)", callback_data="files_skip")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_order")
    )
    return builder.as_markup()


def get_order_summary_kb() -> InlineKeyboardMarkup:
    """Клавиатура для сводки заказа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить и отправить", callback_data="confirm_order")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Заполнить заново", callback_data="order_work"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order"),
    )
    return builder.as_markup()


def get_confirm_order_kb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_order"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order"),
    )
    return builder.as_markup()


# =============================================================================
# ОПЛАТА (для пользователя)
# =============================================================================

def get_payment_kb(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для оплаты заказа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Оплатить", callback_data=f"pay_order_{order_id}")
    )
    builder.row(
        InlineKeyboardButton(text="❓ Вопрос по цене", callback_data="support")
    )
    return builder.as_markup()


# =============================================================================
# АДМИН-ПАНЕЛЬ
# =============================================================================

def get_admin_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню админки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📂 Активные заказы", callback_data="admin_orders")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
    )
    return builder.as_markup()


def get_admin_orders_kb(orders: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком заказов для админа"""
    builder = InlineKeyboardBuilder()

    for order in orders:
        # Обрезаем тему до 20 символов
        subject_short = order.subject[:20] + "..." if len(order.subject) > 20 else order.subject
        status_emoji = "🆕" if order.status == "new" else "⏳"
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} №{order.id} | {subject_short}",
                callback_data=f"admin_order_{order.id}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    return builder.as_markup()


def get_admin_order_kb(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с заказом для админа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📎 Получить файлы", callback_data=f"admin_files_{order_id}")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Назвать цену", callback_data=f"admin_set_price_{order_id}")
    )
    builder.row(
        InlineKeyboardButton(text="✅ В работу", callback_data=f"admin_in_progress_{order_id}"),
        InlineKeyboardButton(text="✔️ Выполнен", callback_data=f"admin_complete_{order_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{order_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 К списку", callback_data="admin_orders")
    )
    return builder.as_markup()


def get_admin_back_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в админ-меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    return builder.as_markup()


def get_admin_cancel_kb() -> InlineKeyboardMarkup:
    """Кнопка отмены действия в админке"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_orders")
    )
    return builder.as_markup()
