"""
Обработка оплаты заказов (заглушка)
"""

import logging
import os

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Order
from config import config

router = Router(name="user_payment")
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("pay_order_"))
async def process_payment(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """
    Обработка оплаты заказа (заглушка).
    В реальном проекте здесь будет интеграция с платёжной системой.
    """
    await callback.answer("💳 Обрабатываем оплату...")

    # Извлекаем ID заказа
    order_id = int(callback.data.split("_")[-1])

    # Получаем заказ
    stmt = (
        select(Order)
        .options(selectinload(Order.user))
        .where(Order.id == order_id)
    )
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        await callback.message.answer("❌ Заказ не найден!")
        return

    # Проверяем, что заказ в статусе ожидания оплаты
    if order.status != "pending_payment":
        await callback.message.answer(
            "⚠️ Этот заказ уже оплачен или находится в другом статусе."
        )
        return

    # === ЗАГЛУШКА: Имитируем успешную оплату ===
    order.status = "paid"
    order.paid_amount = order.price  # Считаем, что оплачена полная сумма

    # Удаляем сообщение с кнопкой оплаты
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Отправляем пользователю подтверждение с фото
    success_text = f"""🤝 <b>Оплата прошла!</b>

💰 Заказ №{order_id} оплачен на сумму <b>{order.price}₽</b>

Шеф уже начал работу над твоим заказом.
Жди вестей, партнёр! 🤠

➖➖➖➖➖➖➖➖➖➖
<i>Мы уведомим тебя, когда работа будет готова.</i>"""

    photo_path = "assets/payment_success.jpg"
    try:
        if os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=success_text,
                parse_mode="HTML",
            )
        else:
            await callback.message.answer(
                text=success_text,
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error(f"Ошибка отправки подтверждения оплаты: {e}")
        await callback.message.answer(
            text=success_text,
            parse_mode="HTML",
        )

    # === Уведомляем всех админов ===
    admin_text = f"""💰 <b>ДЗЫНЬ! Заказ №{order_id} оплачен!</b>

👤 Клиент: {order.user.first_name} (@{order.user.username or '—'})
💸 Сумма: <b>{order.price}₽</b>
📋 Тема: {order.subject[:80]}...

🚀 Работаем, Шеф!"""

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить админа {admin_id}: {e}")

    logger.info(f"Заказ №{order_id} оплачен пользователем {order.user.telegram_id}")
