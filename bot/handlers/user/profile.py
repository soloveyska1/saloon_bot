"""
Хендлер профиля пользователя
Личное дело ковбоя
"""

from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_profile_kb
from database.models import User, Order

router = Router(name="profile")

# Путь к изображению профиля
ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"
PROFILE_IMAGE = ASSETS_DIR / "profile.jpg"

# Названия рангов на русском
RANK_NAMES = {
    "greenhorn": "🌱 Новичок (Greenhorn)",
    "cowboy": "🤠 Ковбой (Cowboy)",
    "ranger": "⭐ Рейнджер (Ranger)",
    "sheriff": "🎖 Шериф (Sheriff)",
    "legend": "👑 Легенда (Legend)",
}


@router.callback_query(F.data == "profile")
async def show_profile(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """
    Показать личное дело ковбоя
    """
    await callback.answer()

    # Форматируем дату регистрации
    date_joined = user.created_at.strftime("%d.%m.%Y")

    # Получаем название ранга
    rank_display = RANK_NAMES.get(user.rank, user.rank)

    # Формируем имя для отображения
    display_name = user.username or user.first_name

    # Получаем username бота для реферальной ссылки
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={user.telegram_id}"

    # Получаем последние 5 заказов пользователя
    stmt = (
        select(Order)
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(5)
    )
    result = await session.execute(stmt)
    orders = result.scalars().all()

    # Формируем историю заказов
    if orders:
        orders_text = "\n📂 <b>Твои заказы:</b>\n"
        for i, order in enumerate(orders, 1):
            # Сокращаем тему
            subject_short = order.subject[:30] + "..." if len(order.subject) > 30 else order.subject
            orders_text += f"{i}. {order.work_type_name} — {order.status_emoji} {order.status_name}\n"
            orders_text += f"   <i>{subject_short}</i>\n"
    else:
        orders_text = "\n<i>📋 История заказов пуста... пока что.</i>\n"

    caption = f"""📂 <b>ЛИЧНОЕ ДЕЛО: {display_name}</b>
➖➖➖➖➖➖➖➖➖➖
🆔 ID: <code>{user.telegram_id}</code>
📅 В банде с: <b>{date_joined}</b>
⭐️ Ранг: <b>{rank_display}</b>
💰 Баланс: <b>{user.balance}</b> руб.
🎁 Бонусы: <b>{user.bonus_balance}</b> монет
➖➖➖➖➖➖➖➖➖➖
🔗 <b>Твоя реферальная ссылка:</b>
<code>{referral_link}</code>
<i>Приглашай друзей и получай бонусы!</i>
➖➖➖➖➖➖➖➖➖➖
{orders_text}
<i>Выполняй заказы — повышай ранг и получай бонусы!</i>"""

    keyboard = get_profile_kb(orders)

    # Отправляем фото или редактируем текст
    if PROFILE_IMAGE.exists():
        photo = FSInputFile(PROFILE_IMAGE)

        # Удаляем старое сообщение и отправляем новое с фото
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        # Fallback: редактируем текст (если было текстовое сообщение)
        # или удаляем и отправляем новое
        try:
            await callback.message.edit_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except Exception:
            await callback.message.delete()
            await callback.message.answer(
                text=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
