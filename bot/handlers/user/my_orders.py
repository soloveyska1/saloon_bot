"""
Просмотр своих заказов пользователем
"""

import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_my_order_kb
from database.models import Order, User

router = Router(name="my_orders")
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("my_order_"))
async def show_my_order(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    """Показать детали своего заказа"""
    await callback.answer()

    order_id = int(callback.data.split("_")[-1])

    # Получаем заказ (проверяем, что он принадлежит пользователю)
    stmt = (
        select(Order)
        .where(Order.id == order_id, Order.user_id == user.id)
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
        "paid": "💰 Оплачен",
        "in_progress": "🔄 В работе",
        "completed": "✅ Готов",
        "cancelled": "❌ Отменён",
    }

    # Цена
    price_str = f"{order.price}₽" if order.price else "—"

    text = f"""📋 <b>ЗАКАЗ №{order.id}</b>
➖➖➖➖➖➖➖➖➖➖

📝 <b>Тип:</b> {order.work_type_name}
📚 <b>Тема:</b>
<i>{order.subject[:200]}</i>

⏰ <b>Срочность:</b> {order.deadline_name}
💰 <b>Цена:</b> {price_str}
🕐 <b>Статус:</b> {status_names.get(order.status, order.status)}

📅 <b>Создан:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}"""

    # Если есть финальный файл
    if order.final_file_id:
        text += f"\n\n📎 <b>Файл:</b> {order.final_file_name or 'Готовая работа'}"

    # Определяем, есть ли файл для скачивания
    has_file = bool(order.final_file_id)

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_my_order_kb(order_id, has_file),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_my_order_kb(order_id, has_file),
        )


@router.callback_query(F.data.startswith("download_work_"))
async def download_work(callback: CallbackQuery, user: User, session: AsyncSession, bot: Bot) -> None:
    """Скачать готовую работу"""
    order_id = int(callback.data.split("_")[-1])

    # Получаем заказ (проверяем принадлежность)
    stmt = (
        select(Order)
        .where(Order.id == order_id, Order.user_id == user.id)
    )
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    if not order.final_file_id:
        await callback.answer("Файл ещё не загружен!", show_alert=True)
        return

    await callback.answer("📥 Отправляю файл...")

    try:
        await bot.send_document(
            chat_id=callback.from_user.id,
            document=order.final_file_id,
            caption=f"📄 {order.final_file_name or 'Готовая работа'}\nЗаказ №{order_id}",
        )
    except Exception as e:
        logger.error(f"Ошибка отправки файла: {e}")
        await callback.message.answer("⚠️ Не удалось отправить файл. Попробуйте позже.")
