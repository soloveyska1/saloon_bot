"""
Админ-панель: Рассылка сообщений
Enterprise CRM Broadcast System
"""

import asyncio
import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.admin import AdminStates
from bot.keyboards.inline import (
    get_admin_broadcast_kb,
    get_admin_broadcast_confirm_kb,
    get_admin_menu_kb,
)
from database.models import User

router = Router(name="admin_broadcast")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "admin_broadcast")
async def show_broadcast_options(callback: CallbackQuery, state: FSMContext) -> None:
    """Показать варианты рассылки"""
    await callback.answer()
    await state.clear()

    text = """📢 <b>РАССЫЛКА СООБЩЕНИЙ</b>
➖➖➖➖➖➖➖➖➖➖

Выберите аудиторию для рассылки:

• 📨 <b>Всем</b> — Все пользователи
• 🤠 <b>Клиенты</b> — Только со статусом Client
• ⭐ <b>VIP</b> — Только VIP пользователи

<i>⚠️ Рассылка может занять несколько минут</i>"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_broadcast_kb(),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_admin_broadcast_kb(),
        )


@router.callback_query(F.data.startswith("admin_broadcast_"))
async def select_broadcast_audience(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор аудитории и запрос текста"""
    if callback.data == "admin_broadcast_confirm":
        return  # Это обработается в confirm_broadcast

    await callback.answer()

    audience = callback.data.split("_")[-1]  # all, clients, vip

    audience_names = {
        "all": "всем пользователям",
        "clients": "клиентам (Client)",
        "vip": "VIP пользователям",
    }

    await state.update_data(broadcast_audience=audience)
    await state.set_state(AdminStates.waiting_for_broadcast_text)

    text = f"""📢 <b>РАССЫЛКА: {audience_names.get(audience, audience).upper()}</b>
➖➖➖➖➖➖➖➖➖➖

Введите текст для рассылки.

<i>Поддерживается HTML-разметка:</i>
• <code>&lt;b&gt;жирный&lt;/b&gt;</code>
• <code>&lt;i&gt;курсив&lt;/i&gt;</code>
• <code>&lt;code&gt;код&lt;/code&gt;</code>

<i>Отправьте текст сообщения:</i>"""

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


@router.message(AdminStates.waiting_for_broadcast_text, F.text)
async def process_broadcast_text(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка текста рассылки и запрос подтверждения"""
    broadcast_text = message.text

    data = await state.get_data()
    audience = data.get("broadcast_audience", "all")

    # Подсчитываем количество получателей
    if audience == "all":
        count = await session.scalar(
            select(User.id).where(User.status_group != "banned").with_only_columns()
        )
        stmt = select(User).where(User.status_group != "banned")
    elif audience == "clients":
        stmt = select(User).where(User.status_group == "client")
    elif audience == "vip":
        stmt = select(User).where(User.status_group == "vip")
    else:
        stmt = select(User).where(User.status_group != "banned")

    result = await session.execute(stmt)
    users = result.scalars().all()
    recipients_count = len(users)

    await state.update_data(broadcast_text=broadcast_text)

    audience_names = {
        "all": "Всем пользователям",
        "clients": "Клиентам",
        "vip": "VIP пользователям",
    }

    preview_text = broadcast_text[:200] + "..." if len(broadcast_text) > 200 else broadcast_text

    text = f"""📢 <b>ПОДТВЕРЖДЕНИЕ РАССЫЛКИ</b>
➖➖➖➖➖➖➖➖➖➖

📋 <b>Аудитория:</b> {audience_names.get(audience, audience)}
👥 <b>Получателей:</b> {recipients_count}

📝 <b>Превью сообщения:</b>
<blockquote>{preview_text}</blockquote>

➖➖➖➖➖➖➖➖➖➖
<i>Подтвердите отправку:</i>"""

    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=get_admin_broadcast_confirm_kb(),
    )


@router.callback_query(F.data == "admin_broadcast_confirm")
async def confirm_broadcast(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Подтверждение и выполнение рассылки"""
    await callback.answer("🚀 Запуск рассылки...")

    data = await state.get_data()
    audience = data.get("broadcast_audience", "all")
    broadcast_text = data.get("broadcast_text")

    if not broadcast_text:
        await callback.message.edit_text(
            "❌ Текст рассылки не найден. Начните заново.",
            parse_mode="HTML",
            reply_markup=get_admin_menu_kb(),
        )
        await state.clear()
        return

    # Получаем пользователей
    if audience == "all":
        stmt = select(User).where(User.status_group != "banned")
    elif audience == "clients":
        stmt = select(User).where(User.status_group == "client")
    elif audience == "vip":
        stmt = select(User).where(User.status_group == "vip")
    else:
        stmt = select(User).where(User.status_group != "banned")

    result = await session.execute(stmt)
    users = result.scalars().all()

    await state.clear()

    # Обновляем сообщение
    await callback.message.edit_text(
        f"🚀 <b>Рассылка запущена!</b>\n\n"
        f"📤 Отправка сообщений: 0/{len(users)}...",
        parse_mode="HTML",
    )

    # Выполняем рассылку
    success = 0
    failed = 0

    for i, user in enumerate(users):
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=broadcast_text,
                parse_mode="HTML",
            )
            success += 1
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user.telegram_id}: {e}")
            failed += 1

        # Обновляем прогресс каждые 10 сообщений
        if (i + 1) % 10 == 0:
            try:
                await callback.message.edit_text(
                    f"🚀 <b>Рассылка в процессе...</b>\n\n"
                    f"📤 Отправлено: {i + 1}/{len(users)}\n"
                    f"✅ Успешно: {success}\n"
                    f"❌ Ошибок: {failed}",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        # Задержка для избежания flood control
        await asyncio.sleep(0.05)

    # Итоговый отчёт
    text = f"""✅ <b>РАССЫЛКА ЗАВЕРШЕНА!</b>
➖➖➖➖➖➖➖➖➖➖

📊 <b>Статистика:</b>
• Всего: {len(users)}
• ✅ Успешно: {success}
• ❌ Ошибок: {failed}

<i>Сообщение доставлено {success} пользователям.</i>"""

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=get_admin_menu_kb(),
    )

    logger.info(f"Рассылка завершена: {success} успешно, {failed} ошибок")
