"""
Админ-панель: Главное меню
"""

from pathlib import Path

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_admin_menu_kb
from database.models import Order

router = Router(name="admin_menu")

# Путь к изображениям
ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"
ADMIN_PANEL_IMAGE = ASSETS_DIR / "admin_panel.jpg"


async def get_orders_count(session: AsyncSession) -> dict:
    """Получить количество заказов по статусам"""
    # Новые заказы
    new_count = await session.scalar(
        select(func.count(Order.id)).where(Order.status == "new")
    )
    # Ожидают оплаты
    pending_count = await session.scalar(
        select(func.count(Order.id)).where(Order.status == "pending_payment")
    )
    # В работе
    in_progress_count = await session.scalar(
        select(func.count(Order.id)).where(Order.status == "in_progress")
    )
    # Всего
    total_count = await session.scalar(select(func.count(Order.id)))

    return {
        "new": new_count or 0,
        "pending": pending_count or 0,
        "in_progress": in_progress_count or 0,
        "total": total_count or 0,
    }


@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession) -> None:
    """
    Вход в админ-панель
    Команда: /admin
    """
    counts = await get_orders_count(session)

    text = f"""🕵️‍♂️ <b>КАБИНЕТ ШЕФА</b>
➖➖➖➖➖➖➖➖➖➖

📊 <b>Статистика заказов:</b>
• 🆕 Новых: <b>{counts['new']}</b>
• ⏳ Ожидают оплаты: <b>{counts['pending']}</b>
• 🔄 В работе: <b>{counts['in_progress']}</b>
• 📦 Всего: <b>{counts['total']}</b>

➖➖➖➖➖➖➖➖➖➖

<i>Выберите действие, Шеф:</i>"""

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
    """Показать главное меню админки"""
    await callback.answer()

    counts = await get_orders_count(session)

    text = f"""🕵️‍♂️ <b>КАБИНЕТ ШЕФА</b>
➖➖➖➖➖➖➖➖➖➖

📊 <b>Статистика заказов:</b>
• 🆕 Новых: <b>{counts['new']}</b>
• ⏳ Ожидают оплаты: <b>{counts['pending']}</b>
• 🔄 В работе: <b>{counts['in_progress']}</b>
• 📦 Всего: <b>{counts['total']}</b>

➖➖➖➖➖➖➖➖➖➖

<i>Выберите действие, Шеф:</i>"""

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


@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery) -> None:
    """Заглушка для статистики"""
    await callback.answer("📊 Статистика будет в следующем обновлении!", show_alert=True)


@router.callback_query(F.data == "admin_broadcast")
async def show_admin_broadcast(callback: CallbackQuery) -> None:
    """Заглушка для рассылки"""
    await callback.answer("📢 Рассылка будет в следующем обновлении!", show_alert=True)
