"""
Админ-панель: Управление пользователями
Баланс, бан/разбан, логирование
"""

import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services import log_payment, log_to_channel, deposit
from bot.keyboards.inline import get_admin_back_kb

router = Router(name="admin_users")
logger = logging.getLogger(__name__)


class AdminUserStates(StatesGroup):
    """Состояния для управления пользователями"""
    waiting_for_user_id = State()
    waiting_for_balance_amount = State()


# =============================================================================
# ИЗМЕНЕНИЕ БАЛАНСА
# =============================================================================

@router.callback_query(F.data == "admin_add_balance")
async def start_add_balance(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать процесс пополнения баланса пользователя"""
    await callback.answer()
    await state.set_state(AdminUserStates.waiting_for_user_id)
    await state.update_data(action="add_balance")

    text = """💰 <b>ПОПОЛНЕНИЕ БАЛАНСА</b>

Введите Telegram ID пользователя:
<i>(например: 123456789)</i>"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_back_kb(),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_back_kb(),
        )


@router.message(AdminUserStates.waiting_for_user_id, F.text)
async def process_user_id(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка ввода Telegram ID пользователя"""
    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "⚠️ Введите корректный Telegram ID (только цифры)!",
            parse_mode="HTML",
        )
        return

    # Проверяем, существует ли пользователь
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await message.answer(
            f"❌ Пользователь с ID <code>{telegram_id}</code> не найден!",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    action = data.get("action")

    if action == "add_balance":
        await state.update_data(target_user_id=user.id, target_telegram_id=telegram_id, target_name=user.first_name)
        await state.set_state(AdminUserStates.waiting_for_balance_amount)

        await message.answer(
            f"👤 Пользователь: <b>{user.first_name}</b> (@{user.username or '—'})\n"
            f"💰 Текущий баланс: <b>{user.balance} руб.</b>\n\n"
            f"Введите сумму пополнения (целое число):",
            parse_mode="HTML",
        )


@router.message(AdminUserStates.waiting_for_balance_amount, F.text)
async def process_balance_change(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Обработка изменения баланса пользователя"""
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
    except ValueError:
        await message.answer(
            "⚠️ Введите корректную сумму (положительное целое число)!",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    user_id = data.get("target_user_id")
    telegram_id = data.get("target_telegram_id")
    user_name = data.get("target_name")

    # Выполняем пополнение баланса
    try:
        transaction = await deposit(
            session=session,
            user_id=user_id,
            amount=amount,
            description=f"Пополнение от администратора",
        )

        # Логируем в канал
        await log_payment(
            bot=bot,
            user_id=telegram_id,
            user_name=user_name,
            amount=amount,
            transaction_type="deposit",
        )

        await state.clear()

        await message.answer(
            f"✅ Баланс пополнен!\n\n"
            f"👤 Пользователь: <b>{user_name}</b>\n"
            f"💵 Сумма: <b>+{amount} руб.</b>\n"
            f"🧾 Транзакция: <code>#{transaction.id}</code>",
            parse_mode="HTML",
        )

        # Уведомляем пользователя
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=f"💰 <b>Баланс пополнен!</b>\n\n"
                     f"Сумма: <b>+{amount} руб.</b>\n\n"
                     f"<i>Спасибо, что с нами!</i> 🤠",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя: {e}")

    except Exception as e:
        logger.error(f"Ошибка пополнения баланса: {e}")
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()


# =============================================================================
# БАН / РАЗБАН ПОЛЬЗОВАТЕЛЕЙ
# =============================================================================

@router.callback_query(F.data.startswith("admin_ban_user_"))
async def ban_user(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Заблокировать пользователя"""
    telegram_id = int(callback.data.split("_")[-1])

    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    # Устанавливаем статус banned
    user.status_group = "banned"

    await callback.answer(f"🚫 Пользователь заблокирован!")

    # Логируем в канал
    await log_to_channel(
        bot=bot,
        event_type="admin",
        message=f"🚫 <b>Пользователь заблокирован</b>\n"
                f"Админ заблокировал пользователя.",
        tags=["ban", "admin_action"],
        user_id=telegram_id,
        user_name=user.first_name,
    )

    logger.info(f"Пользователь {telegram_id} заблокирован")


@router.callback_query(F.data.startswith("admin_unban_user_"))
async def unban_user(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Разблокировать пользователя"""
    telegram_id = int(callback.data.split("_")[-1])

    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    # Снимаем бан
    user.status_group = "client"

    await callback.answer(f"✅ Пользователь разблокирован!")

    # Логируем в канал
    await log_to_channel(
        bot=bot,
        event_type="admin",
        message=f"✅ <b>Пользователь разблокирован</b>\n"
                f"Админ снял блокировку с пользователя.",
        tags=["unban", "admin_action"],
        user_id=telegram_id,
        user_name=user.first_name,
    )

    logger.info(f"Пользователь {telegram_id} разблокирован")
