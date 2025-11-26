"""
Transaction Service - Управление транзакциями и балансом
Enterprise CRM Transaction System
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Transaction

logger = logging.getLogger(__name__)


class InsufficientBalanceError(Exception):
    """Исключение при недостаточном балансе"""
    pass


class UserNotFoundError(Exception):
    """Исключение когда пользователь не найден"""
    pass


async def get_user_balance(session: AsyncSession, user_id: int) -> int:
    """
    Получить текущий баланс пользователя

    Args:
        session: Сессия БД
        user_id: ID пользователя в БД (не telegram_id!)

    Returns:
        int: Текущий баланс
    """
    stmt = select(User.balance).where(User.id == user_id)
    result = await session.execute(stmt)
    balance = result.scalar_one_or_none()

    if balance is None:
        raise UserNotFoundError(f"Пользователь с ID {user_id} не найден")

    return balance


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> Optional[User]:
    """
    Получить пользователя по Telegram ID

    Args:
        session: Сессия БД
        telegram_id: Telegram ID пользователя

    Returns:
        User или None
    """
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_transaction(
    session: AsyncSession,
    user_id: int,
    amount: int,
    transaction_type: str,
    description: str,
    order_id: Optional[int] = None,
    check_balance: bool = True,
) -> Transaction:
    """
    Создать транзакцию и обновить баланс пользователя

    Выполняет обе операции в одной транзакции БД:
    1. Обновляет баланс пользователя
    2. Создаёт запись Transaction

    Args:
        session: Сессия БД
        user_id: ID пользователя в БД (не telegram_id!)
        amount: Сумма (положительная для пополнения, отрицательная для списания)
        transaction_type: Тип транзакции (deposit, payment, refund, bonus)
        description: Описание транзакции
        order_id: ID связанного заказа (опционально)
        check_balance: Проверять ли достаточность баланса при списании

    Returns:
        Transaction: Созданная транзакция

    Raises:
        InsufficientBalanceError: Если баланса недостаточно для списания
        UserNotFoundError: Если пользователь не найден
    """
    # Получаем пользователя
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UserNotFoundError(f"Пользователь с ID {user_id} не найден")

    # Проверяем баланс при списании
    if check_balance and amount < 0:
        if user.balance + amount < 0:
            raise InsufficientBalanceError(
                f"Недостаточно средств. Баланс: {user.balance}, требуется: {abs(amount)}"
            )

    # Обновляем баланс
    user.balance += amount

    # Создаём запись транзакции
    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        type=transaction_type,
        description=description,
        order_id=order_id,
    )
    session.add(transaction)

    # Flush чтобы получить ID транзакции
    await session.flush()

    logger.info(
        f"Транзакция #{transaction.id}: user_id={user_id}, "
        f"amount={amount}, type={transaction_type}"
    )

    return transaction


async def deposit(
    session: AsyncSession,
    user_id: int,
    amount: int,
    description: str = "Пополнение баланса",
) -> Transaction:
    """
    Пополнить баланс пользователя

    Args:
        session: Сессия БД
        user_id: ID пользователя в БД
        amount: Сумма пополнения (должна быть положительной)
        description: Описание операции

    Returns:
        Transaction: Созданная транзакция
    """
    if amount <= 0:
        raise ValueError("Сумма пополнения должна быть положительной")

    return await add_transaction(
        session=session,
        user_id=user_id,
        amount=amount,
        transaction_type="deposit",
        description=description,
        check_balance=False,
    )


async def pay_for_order(
    session: AsyncSession,
    user_id: int,
    amount: int,
    order_id: int,
    description: Optional[str] = None,
) -> Transaction:
    """
    Оплатить заказ с баланса пользователя

    Args:
        session: Сессия БД
        user_id: ID пользователя в БД
        amount: Сумма к списанию (должна быть положительной)
        order_id: ID заказа
        description: Описание операции

    Returns:
        Transaction: Созданная транзакция

    Raises:
        InsufficientBalanceError: Если баланса недостаточно
    """
    if amount <= 0:
        raise ValueError("Сумма оплаты должна быть положительной")

    desc = description or f"Оплата заказа #{order_id}"

    return await add_transaction(
        session=session,
        user_id=user_id,
        amount=-amount,  # Отрицательная сумма для списания
        transaction_type="payment",
        description=desc,
        order_id=order_id,
        check_balance=True,
    )


async def refund(
    session: AsyncSession,
    user_id: int,
    amount: int,
    order_id: Optional[int] = None,
    description: str = "Возврат средств",
) -> Transaction:
    """
    Вернуть средства пользователю

    Args:
        session: Сессия БД
        user_id: ID пользователя в БД
        amount: Сумма возврата (должна быть положительной)
        order_id: ID заказа (если возврат за заказ)
        description: Описание операции

    Returns:
        Transaction: Созданная транзакция
    """
    if amount <= 0:
        raise ValueError("Сумма возврата должна быть положительной")

    return await add_transaction(
        session=session,
        user_id=user_id,
        amount=amount,
        transaction_type="refund",
        description=description,
        order_id=order_id,
        check_balance=False,
    )


async def add_bonus(
    session: AsyncSession,
    user_id: int,
    amount: int,
    description: str = "Начисление бонуса",
) -> Transaction:
    """
    Начислить бонус пользователю

    Args:
        session: Сессия БД
        user_id: ID пользователя в БД
        amount: Сумма бонуса (должна быть положительной)
        description: Описание операции

    Returns:
        Transaction: Созданная транзакция
    """
    if amount <= 0:
        raise ValueError("Сумма бонуса должна быть положительной")

    return await add_transaction(
        session=session,
        user_id=user_id,
        amount=amount,
        transaction_type="bonus",
        description=description,
        check_balance=False,
    )


async def get_user_transactions(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
    transaction_type: Optional[str] = None,
) -> list[Transaction]:
    """
    Получить историю транзакций пользователя

    Args:
        session: Сессия БД
        user_id: ID пользователя в БД
        limit: Максимальное количество записей
        transaction_type: Фильтр по типу транзакции

    Returns:
        list[Transaction]: Список транзакций
    """
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )

    if transaction_type:
        stmt = stmt.where(Transaction.type == transaction_type)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def calculate_total_spent(session: AsyncSession, user_id: int) -> int:
    """
    Подсчитать общую сумму потраченных средств

    Args:
        session: Сессия БД
        user_id: ID пользователя в БД

    Returns:
        int: Общая сумма (положительное число)
    """
    from sqlalchemy import func as sql_func

    stmt = (
        select(sql_func.sum(Transaction.amount))
        .where(Transaction.user_id == user_id)
        .where(Transaction.type == "payment")
    )
    result = await session.execute(stmt)
    total = result.scalar_one_or_none()

    return abs(total) if total else 0


async def calculate_total_deposited(session: AsyncSession, user_id: int) -> int:
    """
    Подсчитать общую сумму пополнений

    Args:
        session: Сессия БД
        user_id: ID пользователя в БД

    Returns:
        int: Общая сумма пополнений
    """
    from sqlalchemy import func as sql_func

    stmt = (
        select(sql_func.sum(Transaction.amount))
        .where(Transaction.user_id == user_id)
        .where(Transaction.type.in_(["deposit", "refund", "bonus"]))
    )
    result = await session.execute(stmt)
    total = result.scalar_one_or_none()

    return total if total else 0
