"""
Админ-панель: Главное меню (God Mode)
Enterprise CRM Admin Dashboard
"""

from pathlib import Path

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_admin_menu_kb
from database.models import Order, User

router = Router(name="admin_menu")

# Путь к изображениям
ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"
ADMIN_PANEL_IMAGE = ASSETS_DIR / "admin_panel.jpg"


async def get_dashboard_stats(session: AsyncSession) -> dict:
    """Получить статистику для дашборда"""

    # Пользователи
    total_users = await session.scalar(select(func.count(User.id)))

    # Сумма всех балансов
    total_balance = await session.scalar(select(func.sum(User.balance))) or 0

    # Статистика по заказам
    new_orders = await session.scalar(
        select(func.count(Order.id)).where(
            or_(Order.status == "new", Order.status == "pending")
        )
    )
    pending_payment = await session.scalar(
        select(func.count(Order.id)).where(
            or_(Order.status == "pending_payment", Order.status == "payment_wait")
        )
    )
    in_progress = await session.scalar(
        select(func.count(Order.id)).where(
            or_(Order.status == "in_progress", Order.status == "working", Order.status == "paid")
        )
    )
    completed = await session.scalar(
        select(func.count(Order.id)).where(
            or_(Order.status == "completed", Order.status == "ready")
        )
    )
    total_orders = await session.scalar(select(func.count(Order.id)))

    # Общая сумма оплаченных заказов
    total_revenue = await session.scalar(
        select(func.sum(Order.price)).where(
            Order.status.in_(["paid", "in_progress", "working", "completed", "ready"])
        )
    ) or 0

    # Активные пользователи (по статусу)
    clients_count = await session.scalar(
        select(func.count(User.id)).where(User.status_group == "client")
    )
    vip_count = await session.scalar(
        select(func.count(User.id)).where(User.status_group == "vip")
    )

    return {
        "total_users": total_users or 0,
        "total_balance": total_balance,
        "new_orders": new_orders or 0,
        "pending_payment": pending_payment or 0,
        "in_progress": in_progress or 0,
        "completed": completed or 0,
        "total_orders": total_orders or 0,
        "total_revenue": total_revenue,
        "clients": clients_count or 0,
        "vip": vip_count or 0,
    }


def get_admin_menu_text(stats: dict) -> str:
    """Сформировать текст меню админки"""
    return f"""🕵️‍♂️ <b>КАБИНЕТ ШЕФА</b>
<i>Enterprise CRM Dashboard</i>
➖➖➖➖➖➖➖➖➖➖

👥 <b>Пользователи:</b>
• Всего: <b>{stats['total_users']}</b>
• Клиенты: <b>{stats['clients']}</b>
• VIP: <b>{stats['vip']}</b>

📦 <b>Заказы:</b>
• 🆕 Новых: <b>{stats['new_orders']}</b>
• ⏳ Ожидают оплаты: <b>{stats['pending_payment']}</b>
• 🔄 В работе: <b>{stats['in_progress']}</b>
• ✅ Выполнено: <b>{stats['completed']}</b>

💰 <b>Финансы:</b>
• Балансы юзеров: <b>{stats['total_balance']:,} ₽</b>
• Выручка: <b>{stats['total_revenue']:,} ₽</b>

➖➖➖➖➖➖➖➖➖➖

<i>Выберите действие, Шеф:</i>"""


@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession) -> None:
    """
    Вход в админ-панель
    Команда: /admin
    """
    stats = await get_dashboard_stats(session)
    text = get_admin_menu_text(stats)

    if ADMIN_PANEL_IMAGE.exists():
        photo = FSInputFile(ADMIN_PANEL_IMAGE)
        await message.answer_photo(
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_kb(),
        )
    else:
        await message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_kb(),
        )


@router.callback_query(F.data == "admin_menu")
async def show_admin_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    """Показать главное меню админки (возврат из других разделов)"""
    await callback.answer()

    stats = await get_dashboard_stats(session)
    text = get_admin_menu_text(stats)

    # Всегда удаляем старое сообщение и отправляем новое
    await callback.message.delete()

    if ADMIN_PANEL_IMAGE.exists():
        photo = FSInputFile(ADMIN_PANEL_IMAGE)
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_kb(),
        )
    else:
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_kb(),
        )


@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    """Показать детальную статистику"""
    await callback.answer()

    stats = await get_dashboard_stats(session)

    text = f"""📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>
➖➖➖➖➖➖➖➖➖➖

👥 <b>ПОЛЬЗОВАТЕЛИ</b>
├ Всего зарегистрировано: <b>{stats['total_users']}</b>
├ Со статусом Guest: <b>{stats['total_users'] - stats['clients'] - stats['vip']}</b>
├ Со статусом Client: <b>{stats['clients']}</b>
└ Со статусом VIP: <b>{stats['vip']}</b>

📦 <b>ЗАКАЗЫ</b>
├ Всего заказов: <b>{stats['total_orders']}</b>
├ Новых/Ожидает оценки: <b>{stats['new_orders']}</b>
├ Ожидают оплаты: <b>{stats['pending_payment']}</b>
├ В работе: <b>{stats['in_progress']}</b>
└ Завершено: <b>{stats['completed']}</b>

💰 <b>ФИНАНСЫ</b>
├ Сумма балансов: <b>{stats['total_balance']:,} ₽</b>
└ Общая выручка: <b>{stats['total_revenue']:,} ₽</b>

➖➖➖➖➖➖➖➖➖➖
<i>Обновлено только что</i>"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_kb(),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_menu_kb(),
        )
