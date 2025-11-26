"""
Хендлер профиля пользователя
Личное дело ковбоя
"""

from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from bot.keyboards.inline import get_back_kb
from database.models import User

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
async def show_profile(callback: CallbackQuery, user: User) -> None:
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

    caption = f"""📂 <b>ЛИЧНОЕ ДЕЛО: {display_name}</b>
➖➖➖➖➖➖➖➖➖➖
🆔 ID: <code>{user.telegram_id}</code>
📅 В банде с: <b>{date_joined}</b>
⭐️ Ранг: <b>{rank_display}</b>
💰 Бонусы: <b>{user.bonus_balance}</b> монет
➖➖➖➖➖➖➖➖➖➖

<i>📋 История заказов пуста... пока что.</i>

<i>Выполняй заказы — повышай ранг и получай бонусы!</i>"""

    keyboard = get_back_kb(callback_data="main_menu")

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
