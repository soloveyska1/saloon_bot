"""
FSM состояния для админки
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
