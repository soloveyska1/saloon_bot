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
