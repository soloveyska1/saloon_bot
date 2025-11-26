"""
FSM состояния для админки
Enterprise CRM Admin States
"""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """Состояния админ-панели"""

    # Ожидание ввода цены для заказа
    waiting_for_price = State()

    # Ожидание причины отказа
    waiting_for_reject_reason = State()

    # Ожидание текста рассылки
    waiting_for_broadcast = State()

    # Ожидание финального файла (готовой работы)
    waiting_for_final_file = State()

    # === CRM User Management ===
    # Ожидание ввода ID или username для поиска
    waiting_for_user_search = State()

    # Ожидание суммы для изменения баланса
    waiting_for_amount = State()

    # Ожидание текста заметки
    waiting_for_note = State()

    # Ожидание текста рассылки
    waiting_for_broadcast_text = State()
