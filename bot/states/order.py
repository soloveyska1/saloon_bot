"""
FSM состояния для оформления заказа
"""

from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    """Машина состояний для воронки заказа"""

    # Шаг 1: Выбор типа работы
    waiting_for_type = State()

    # Шаг 2: Ввод предмета/темы
    waiting_for_subject = State()

    # Шаг 3: Выбор дедлайна
    waiting_for_deadline = State()

    # Шаг 4: Загрузка файлов (методичка, материалы)
    waiting_for_files = State()

    # Шаг 5: Дополнительные пожелания
    waiting_for_comment = State()

    # Шаг 6: Подтверждение заказа
    waiting_for_confirmation = State()

    # Ожидание чека оплаты
    waiting_for_receipt = State()


class SupportState(StatesGroup):
    """Состояния для обращения в поддержку"""

    # Ожидание сообщения для поддержки
    waiting_for_message = State()
