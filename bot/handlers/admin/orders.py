"""
Админ-панель: Управление заказами
"""

import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.states.admin import AdminStates
from bot.keyboards.inline import (
    get_admin_orders_kb,
    get_admin_order_kb,
    get_admin_cancel_kb,
    get_admin_back_kb,
    get_payment_kb,
)
from database.models import Order, User

router = Router(name="admin_orders")
logger = logging.getLogger(__name__)


# =============================================================================
# СПИСОК ЗАКАЗОВ
# =============================================================================

@router.callback_query(F.data == "admin_orders")
async def show_orders_list(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """Показать список активных заказов"""
    await callback.answer()

    # Сбрасываем состояние, если было
    await state.clear()

    # Получаем заказы со статусами new, pending_payment, in_progress
    stmt = (
        select(Order)
        .where(or_(
            Order.status == "new",
            Order.status == "pending_payment",
            Order.status == "in_progress",
        ))
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(stmt)
    orders = result.scalars().all()

    # Удаляем старое сообщение (это может быть фото или текст)
    await callback.message.delete()

    if not orders:
        text = """📂 <b>АКТИВНЫЕ ЗАКАЗЫ</b>
➖➖➖➖➖➖➖➖➖➖

<i>В Салуне пусто, Шеф.</i>
<i>Ни одного активного заказа.</i>

🤠 Отдыхайте пока!"""
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_back_kb(),
        )
        return

    text = f"""📂 <b>АКТИВНЫЕ ЗАКАЗЫ</b>
➖➖➖➖➖➖➖➖➖➖

Найдено заказов: <b>{len(orders)}</b>

<i>Выберите заказ для просмотра:</i>"""

    await callback.message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=get_admin_orders_kb(orders),
    )


# =============================================================================
# КАРТОЧКА ЗАКАЗА
# =============================================================================

@router.callback_query(F.data.startswith("admin_order_"))
async def show_order_card(callback: CallbackQuery, session: AsyncSession) -> None:
    """Показать карточку заказа"""
    await callback.answer()

    # Извлекаем ID заказа
    order_id = int(callback.data.split("_")[-1])

    # Получаем заказ с пользователем
    stmt = (
        select(Order)
        .options(selectinload(Order.user))
        .where(Order.id == order_id)
    )
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    # Статусы на русском
    status_names = {
        "new": "🆕 Новый",
        "pending_payment": "⏳ Ожидает оплаты",
        "in_progress": "🔄 В работе",
        "review": "👀 На проверке",
        "completed": "✅ Выполнен",
        "cancelled": "❌ Отменён",
    }

    # Количество файлов
    files_count = order.files_count

    # Цена
    price_str = f"{order.price} руб." if order.price else "Не назначена"

    text = f"""📋 <b>ЗАКАЗ №{order.id}</b>
➖➖➖➖➖➖➖➖➖➖

👤 <b>Клиент:</b> {order.user.first_name}
🔗 <b>Username:</b> @{order.user.username or '—'}
🆔 <b>Telegram:</b> <code>{order.user.telegram_id}</code>

📝 <b>Тип:</b> {order.work_type_name}
📚 <b>Тема:</b>
<i>{order.subject[:300]}</i>

⏰ <b>Срочность:</b> {order.deadline_name}
📎 <b>Файлов:</b> {files_count}
💰 <b>Цена:</b> {price_str}

🕐 <b>Статус:</b> {status_names.get(order.status, order.status)}
📅 <b>Создан:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}

➖➖➖➖➖➖➖➖➖➖
<i>Выберите действие:</i>"""

    # Пробуем отредактировать текст (если текущее сообщение текстовое)
    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_order_kb(order_id),
        )
    except Exception:
        # Если не получилось (например, было фото), удаляем и отправляем новое
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_order_kb(order_id),
        )


# =============================================================================
# ПОЛУЧИТЬ ФАЙЛЫ
# =============================================================================

@router.callback_query(F.data.startswith("admin_files_"))
async def send_order_files(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """Отправить файлы заказа админу"""
    order_id = int(callback.data.split("_")[-1])

    # Получаем заказ
    stmt = select(Order).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    file_ids_list = order.file_ids_list

    if not file_ids_list and not order.voice_file_id:
        await callback.answer("К заказу не прикреплено файлов", show_alert=True)
        return

    files_count = len(file_ids_list) + (1 if order.voice_file_id else 0)
    await callback.answer(f"Отправляю {files_count} файл(ов)...")

    # Отправляем файлы
    for file_entry in file_ids_list:
        try:
            if file_entry.startswith("photo:"):
                file_id = file_entry.split(":")[1]
                await bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=file_id,
                    caption=f"📸 Фото к заказу №{order_id}",
                )
            elif file_entry.startswith("doc:"):
                parts = file_entry.split(":")
                file_id = parts[1]
                file_name = parts[2] if len(parts) > 2 else "document"
                await bot.send_document(
                    chat_id=callback.from_user.id,
                    document=file_id,
                    caption=f"📄 {file_name} (Заказ №{order_id})",
                )
        except Exception as e:
            logger.error(f"Ошибка отправки файла: {e}")
            await bot.send_message(
                chat_id=callback.from_user.id,
                text=f"⚠️ Не удалось отправить файл: {file_entry[:50]}",
            )

    # Если было голосовое сообщение
    if order.voice_file_id:
        try:
            await bot.send_voice(
                chat_id=callback.from_user.id,
                voice=order.voice_file_id,
                caption=f"🎙 Голосовое к заказу №{order_id}",
            )
        except Exception as e:
            logger.error(f"Ошибка отправки голосового: {e}")


# =============================================================================
# НАЗНАЧИТЬ ЦЕНУ
# =============================================================================

@router.callback_query(F.data.startswith("admin_set_price_"))
async def start_set_price(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать процесс назначения цены"""
    await callback.answer()

    order_id = int(callback.data.split("_")[-1])

    # Сохраняем ID заказа в состояние
    await state.update_data(order_id=order_id)
    await state.set_state(AdminStates.waiting_for_price)

    text = f"""💰 <b>НАЗНАЧЕНИЕ ЦЕНЫ</b>

Заказ №{order_id}

Введите цену в рублях (только число):
<i>Например: 5000</i>"""

    # Пробуем отредактировать, если не выйдет - удаляем и отправляем
    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_cancel_kb(),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_cancel_kb(),
        )


@router.message(AdminStates.waiting_for_price, F.text)
async def process_price(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Обработка введённой цены"""
    # Проверяем, что это число
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError("Цена должна быть положительной")
    except ValueError:
        await message.answer(
            "⚠️ Введите корректную цену (целое положительное число)!",
            parse_mode="HTML",
        )
        return

    # Получаем ID заказа из состояния
    data = await state.get_data()
    order_id = data.get("order_id")

    # Обновляем заказ
    stmt = (
        select(Order)
        .options(selectinload(Order.user))
        .where(Order.id == order_id)
    )
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        await message.answer("❌ Заказ не найден!")
        await state.clear()
        return

    # Устанавливаем цену и меняем статус
    order.price = price
    order.status = "pending_payment"

    # Очищаем состояние
    await state.clear()

    # Уведомляем админа
    await message.answer(
        f"✅ Цена <b>{price} руб.</b> установлена для заказа №{order_id}!\n\n"
        f"Уведомление отправлено клиенту.",
        parse_mode="HTML",
    )

    # Отправляем уведомление пользователю
    user_text = f"""⚡️ <b>Шеф оценил твой заказ №{order_id}!</b>

💰 <b>Цена:</b> {price} руб.

📋 <b>Тема:</b> {order.subject[:100]}

➖➖➖➖➖➖➖➖➖➖

Для начала работы внеси предоплату 50%.
Остаток — после получения готовой работы.

<i>Жми кнопку для оплаты:</i> 👇"""

    try:
        await bot.send_message(
            chat_id=order.user.telegram_id,
            text=user_text,
            parse_mode="HTML",
            reply_markup=get_payment_kb(order_id),
        )
        logger.info(f"Уведомление о цене отправлено пользователю {order.user.telegram_id}")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление пользователю: {e}")
        await message.answer(f"⚠️ Не удалось уведомить клиента: {e}")


# =============================================================================
# ИЗМЕНЕНИЕ СТАТУСОВ
# =============================================================================

@router.callback_query(F.data.startswith("admin_in_progress_"))
async def set_in_progress(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """Перевести заказ в работу"""
    order_id = int(callback.data.split("_")[-1])

    stmt = select(Order).options(selectinload(Order.user)).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    order.status = "in_progress"
    await callback.answer(f"✅ Заказ №{order_id} переведён в работу!")

    # Уведомляем пользователя
    try:
        await bot.send_message(
            chat_id=order.user.telegram_id,
            text=f"🔄 <b>Заказ №{order_id} взят в работу!</b>\n\n"
                 f"Ковбой, твоя работа уже готовится. "
                 f"Мы сообщим, когда всё будет готово!",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")

    # Обновляем карточку
    await show_order_card(callback, session)


@router.callback_query(F.data.startswith("admin_complete_"))
async def set_completed(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """Пометить заказ как выполненный"""
    order_id = int(callback.data.split("_")[-1])

    stmt = select(Order).options(selectinload(Order.user)).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    order.status = "completed"
    await callback.answer(f"✅ Заказ №{order_id} выполнен!")

    # Уведомляем пользователя
    try:
        await bot.send_message(
            chat_id=order.user.telegram_id,
            text=f"🎉 <b>Заказ №{order_id} выполнен!</b>\n\n"
                 f"Йо-хо, партнёр! Твоя работа готова!\n"
                 f"Шеф скоро отправит тебе результат.\n\n"
                 f"<i>Спасибо, что выбрал Академический Салун!</i> 🤠",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")

    # Обновляем карточку
    await show_order_card(callback, session)


@router.callback_query(F.data.startswith("admin_reject_"))
async def reject_order(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    """Отклонить заказ"""
    order_id = int(callback.data.split("_")[-1])

    stmt = select(Order).options(selectinload(Order.user)).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    order.status = "cancelled"
    await callback.answer(f"❌ Заказ №{order_id} отклонён!")

    # Уведомляем пользователя
    try:
        await bot.send_message(
            chat_id=order.user.telegram_id,
            text=f"😔 <b>Заказ №{order_id} отклонён</b>\n\n"
                 f"К сожалению, мы не можем взять этот заказ в работу.\n\n"
                 f"<i>Свяжитесь с нами для уточнения деталей.</i>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")

    # Возвращаемся к списку заказов
    await show_orders_list(callback, session, state)
