"""
Админ-панель: Управление пользователями (CRM)
Enterprise CRM User Management
"""

import logging
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.admin import AdminStates
from bot.keyboards.inline import (
    get_admin_user_search_cancel_kb,
    get_admin_user_dossier_kb,
    get_admin_user_status_kb,
    get_admin_balance_cancel_kb,
    get_admin_menu_kb,
    get_admin_orders_kb,
)
from database.models import User, Order, Transaction
from services.transaction_service import add_transaction

router = Router(name="admin_users")
logger = logging.getLogger(__name__)


# =============================================================================
# ПОИСК ПОЛЬЗОВАТЕЛЯ
# =============================================================================

@router.callback_query(F.data == "admin_search_user")
async def start_user_search(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать поиск пользователя"""
    await callback.answer()
    await state.clear()
    await state.set_state(AdminStates.waiting_for_user_search)

    text = """🔍 <b>ПОИСК ПОЛЬЗОВАТЕЛЯ</b>
➖➖➖➖➖➖➖➖➖➖

Введите для поиска:
• <b>Telegram ID</b> (число)
• <b>Username</b> (без @)

<i>Например: 123456789 или ivan_petrov</i>"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_user_search_cancel_kb(),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_user_search_cancel_kb(),
        )


@router.message(AdminStates.waiting_for_user_search, F.text)
async def process_user_search(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка поиска пользователя"""
    search_query = message.text.strip().lstrip("@")

    # Пробуем найти по ID или username
    user = None

    # Если это число — ищем по telegram_id
    if search_query.isdigit():
        telegram_id = int(search_query)
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    # Если не нашли по ID — ищем по username
    if not user:
        stmt = select(User).where(User.username == search_query)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        await message.answer(
            f"❌ Пользователь <code>{search_query}</code> не найден.\n\n"
            f"Попробуйте другой ID или username.",
            parse_mode="HTML",
            reply_markup=get_admin_user_search_cancel_kb(),
        )
        return

    # Нашли пользователя — показываем досье
    await state.clear()
    await show_user_dossier(message, user, session)


async def show_user_dossier(
    message_or_callback,
    user: User,
    session: AsyncSession,
    edit: bool = False,
) -> None:
    """Показать досье пользователя"""

    # Получаем количество заказов
    orders_count = await session.scalar(
        select(Order.id).where(Order.user_id == user.id).with_only_columns()
    )
    orders_stmt = select(Order).where(Order.user_id == user.id)
    orders_result = await session.execute(orders_stmt)
    orders = orders_result.scalars().all()
    orders_count = len(orders)

    # Получаем последние транзакции
    trans_stmt = (
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(3)
    )
    trans_result = await session.execute(trans_stmt)
    transactions = trans_result.scalars().all()

    # Статус группы с эмодзи
    status_emoji = {
        "guest": "👤 Guest",
        "client": "🤠 Client",
        "vip": "⭐ VIP",
        "banned": "🚫 Banned",
    }
    status_display = status_emoji.get(user.status_group, user.status_group)

    # Реферер
    referrer_text = "—"
    if user.referrer_id:
        referrer_text = f"<code>{user.referrer_id}</code>"

    # Последняя активность
    last_active_text = "—"
    if user.last_active:
        last_active_text = user.last_active.strftime("%d.%m.%Y %H:%M")

    # Дата регистрации
    created_text = user.created_at.strftime("%d.%m.%Y %H:%M") if user.created_at else "—"

    # Заметки админа
    notes_text = user.admin_notes or "<i>Заметок нет</i>"

    # Последние транзакции
    trans_text = ""
    if transactions:
        trans_text = "\n\n💳 <b>Последние транзакции:</b>\n"
        for t in transactions:
            sign = "+" if t.amount >= 0 else ""
            trans_text += f"• {t.type_emoji} {sign}{t.amount}₽ — {t.description[:30]}\n"

    # Проверяем, забанен ли
    is_banned = user.status_group == "banned"

    text = f"""📋 <b>ДОСЬЕ ПОЛЬЗОВАТЕЛЯ</b>
➖➖➖➖➖➖➖➖➖➖

👤 <b>Имя:</b> {user.first_name} {user.last_name or ''}
📛 <b>Username:</b> @{user.username or '—'}
🆔 <b>Telegram ID:</b> <code>{user.telegram_id}</code>
🔗 <b>Magic Link:</b> <a href="tg://user?id={user.telegram_id}">Открыть чат</a>

💰 <b>Баланс:</b> <code>{user.balance}</code> ₽
📊 <b>Статус:</b> {status_display}
🤝 <b>Реферер:</b> {referrer_text}
📜 <b>Оферта:</b> {'✅ Принята' if user.terms_accepted else '❌ Не принята'}

📅 <b>Регистрация:</b> {created_text}
🕐 <b>Последняя активность:</b> {last_active_text}
📦 <b>Заказов:</b> {orders_count}

📝 <b>Заметка админа:</b>
{notes_text}{trans_text}

➖➖➖➖➖➖➖➖➖➖
<i>Выберите действие:</i>"""

    keyboard = get_admin_user_dossier_kb(user.id, is_banned)

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        # CallbackQuery
        if edit:
            try:
                await message_or_callback.message.edit_text(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception:
                await message_or_callback.message.delete()
                await message_or_callback.message.answer(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
        else:
            await message_or_callback.message.delete()
            await message_or_callback.message.answer(
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )


@router.callback_query(F.data.startswith("admin_view_user_"))
async def view_user_dossier(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Показать досье пользователя по ID"""
    await callback.answer()
    await state.clear()

    user_id = int(callback.data.split("_")[-1])
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    await show_user_dossier(callback, user, session, edit=True)


# =============================================================================
# ИЗМЕНЕНИЕ БАЛАНСА
# =============================================================================

@router.callback_query(F.data.startswith("admin_user_balance_"))
async def start_balance_change(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать изменение баланса"""
    await callback.answer()

    user_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminStates.waiting_for_amount)

    text = """💰 <b>ИЗМЕНЕНИЕ БАЛАНСА</b>
➖➖➖➖➖➖➖➖➖➖

Введите сумму для изменения баланса:
• <b>+500</b> — пополнить на 500₽
• <b>-200</b> — списать 200₽
• <b>1000</b> — пополнить на 1000₽

<i>Введите число со знаком или без:</i>"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_balance_cancel_kb(user_id),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_balance_cancel_kb(user_id),
        )


@router.message(AdminStates.waiting_for_amount, F.text)
async def process_balance_change(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Обработка изменения баланса"""
    try:
        amount = int(message.text.strip().replace("+", ""))
    except ValueError:
        await message.answer(
            "⚠️ Введите корректное число!\n"
            "Например: +500, -200, 1000",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    user_id = data.get("target_user_id")

    # Получаем пользователя
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await message.answer("❌ Пользователь не найден!")
        await state.clear()
        return

    # Определяем тип транзакции
    if amount >= 0:
        trans_type = "deposit"
        description = "Пополнение от администратора"
    else:
        trans_type = "payment"
        description = "Списание администратором"

    # Создаём транзакцию
    try:
        transaction = await add_transaction(
            session=session,
            user_id=user_id,
            amount=amount,
            transaction_type=trans_type,
            description=description,
            check_balance=False,  # Админ может уводить в минус
        )

        await state.clear()

        await message.answer(
            f"✅ <b>Баланс изменён!</b>\n\n"
            f"👤 Пользователь: {user.first_name}\n"
            f"💰 Изменение: <code>{'+' if amount >= 0 else ''}{amount}</code> ₽\n"
            f"💳 Новый баланс: <code>{user.balance}</code> ₽\n"
            f"📝 Транзакция: #{transaction.id}",
            parse_mode="HTML",
            reply_markup=get_admin_user_dossier_kb(user_id, user.status_group == "banned"),
        )

        # Уведомляем пользователя
        try:
            if amount >= 0:
                user_text = f"💰 <b>Ваш баланс пополнен!</b>\n\n+{amount} ₽\nНовый баланс: {user.balance} ₽"
            else:
                user_text = f"💸 <b>С вашего баланса списано:</b>\n\n{amount} ₽\nНовый баланс: {user.balance} ₽"

            await bot.send_message(
                chat_id=user.telegram_id,
                text=user_text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя: {e}")

    except Exception as e:
        logger.error(f"Ошибка при изменении баланса: {e}")
        await message.answer(f"❌ Ошибка: {e}")


# =============================================================================
# ИЗМЕНЕНИЕ ЗАМЕТКИ
# =============================================================================

@router.callback_query(F.data.startswith("admin_user_note_"))
async def start_note_change(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать изменение заметки"""
    await callback.answer()

    user_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminStates.waiting_for_note)

    text = """✏️ <b>РЕДАКТИРОВАНИЕ ЗАМЕТКИ</b>
➖➖➖➖➖➖➖➖➖➖

Введите текст заметки для этого пользователя.

<i>Эта заметка видна только администраторам.</i>

Отправьте текст или <code>-</code> чтобы удалить заметку:"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_balance_cancel_kb(user_id),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_balance_cancel_kb(user_id),
        )


@router.message(AdminStates.waiting_for_note, F.text)
async def process_note_change(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка изменения заметки"""
    note_text = message.text.strip()

    data = await state.get_data()
    user_id = data.get("target_user_id")

    # Получаем пользователя
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await message.answer("❌ Пользователь не найден!")
        await state.clear()
        return

    # Обновляем заметку
    if note_text == "-":
        user.admin_notes = None
        note_display = "удалена"
    else:
        user.admin_notes = note_text
        note_display = f"обновлена"

    await state.clear()

    await message.answer(
        f"✅ <b>Заметка {note_display}!</b>\n\n"
        f"👤 Пользователь: {user.first_name}",
        parse_mode="HTML",
        reply_markup=get_admin_user_dossier_kb(user_id, user.status_group == "banned"),
    )


# =============================================================================
# БАН / РАЗБАН
# =============================================================================

@router.callback_query(F.data.startswith("admin_user_ban_"))
async def ban_user(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """Забанить пользователя"""
    user_id = int(callback.data.split("_")[-1])

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    user.status_group = "banned"
    await callback.answer(f"🚫 Пользователь {user.first_name} забанен!")

    # Уведомляем пользователя
    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text="🚫 <b>Ваш аккаунт заблокирован.</b>\n\n"
                 "Для разблокировки свяжитесь с администрацией.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить пользователя о бане: {e}")

    await show_user_dossier(callback, user, session, edit=True)


@router.callback_query(F.data.startswith("admin_user_unban_"))
async def unban_user(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """Разбанить пользователя"""
    user_id = int(callback.data.split("_")[-1])

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    user.status_group = "guest"
    await callback.answer(f"✅ Пользователь {user.first_name} разбанен!")

    # Уведомляем пользователя
    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text="✅ <b>Ваш аккаунт разблокирован!</b>\n\n"
                 "Добро пожаловать обратно в Салун! 🤠",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить пользователя о разбане: {e}")

    await show_user_dossier(callback, user, session, edit=True)


# =============================================================================
# ИЗМЕНЕНИЕ СТАТУСА
# =============================================================================

@router.callback_query(F.data.startswith("admin_user_status_"))
async def show_status_options(callback: CallbackQuery) -> None:
    """Показать варианты статуса"""
    await callback.answer()

    user_id = int(callback.data.split("_")[-1])

    text = """📊 <b>ИЗМЕНЕНИЕ СТАТУСА</b>
➖➖➖➖➖➖➖➖➖➖

Выберите новый статус пользователя:

• 👤 <b>Guest</b> — Обычный пользователь
• 🤠 <b>Client</b> — Активный клиент
• ⭐ <b>VIP</b> — VIP клиент"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_user_status_kb(user_id),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_user_status_kb(user_id),
        )


@router.callback_query(F.data.startswith("admin_set_status_"))
async def set_user_status(callback: CallbackQuery, session: AsyncSession) -> None:
    """Установить статус пользователя"""
    parts = callback.data.split("_")
    user_id = int(parts[3])
    new_status = parts[4]

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    user.status_group = new_status

    status_names = {"guest": "Guest", "client": "Client", "vip": "VIP"}
    await callback.answer(f"✅ Статус изменён на {status_names.get(new_status, new_status)}!")

    await show_user_dossier(callback, user, session, edit=True)


# =============================================================================
# ЗАКАЗЫ ПОЛЬЗОВАТЕЛЯ
# =============================================================================

@router.callback_query(F.data.startswith("admin_user_orders_"))
async def show_user_orders(callback: CallbackQuery, session: AsyncSession) -> None:
    """Показать заказы пользователя"""
    await callback.answer()

    user_id = int(callback.data.split("_")[-1])

    # Получаем пользователя
    user_stmt = select(User).where(User.id == user_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    # Получаем заказы
    orders_stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    orders_result = await session.execute(orders_stmt)
    orders = orders_result.scalars().all()

    if not orders:
        text = f"""📦 <b>ЗАКАЗЫ ПОЛЬЗОВАТЕЛЯ</b>
➖➖➖➖➖➖➖➖➖➖

👤 {user.first_name} (@{user.username or '—'})

<i>У пользователя нет заказов.</i>"""
    else:
        text = f"""📦 <b>ЗАКАЗЫ ПОЛЬЗОВАТЕЛЯ</b>
➖➖➖➖➖➖➖➖➖➖

👤 {user.first_name} (@{user.username or '—'})
📊 Всего заказов: {len(orders)}

"""
        for order in orders:
            text += f"{order.status_emoji} <b>№{order.id}</b> — {order.status_name}\n"
            text += f"   📝 {order.subject[:40]}...\n"
            text += f"   💰 {order.price or '—'} ₽\n\n"

    keyboard = get_admin_user_dossier_kb(user_id, user.status_group == "banned")

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
