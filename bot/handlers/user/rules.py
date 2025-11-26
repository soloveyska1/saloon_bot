"""
Хендлер правил салуна
Кодекс Салуна
"""

from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from bot.keyboards.inline import get_back_kb

router = Router(name="rules")

# Путь к изображению правил
ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"
RULES_IMAGE = ASSETS_DIR / "rules.jpg"


@router.callback_query(F.data == "rules")
async def show_rules(callback: CallbackQuery) -> None:
    """
    Показать Кодекс Салуна
    """
    await callback.answer()

    caption = """📜 <b>КОДЕКС САЛУНА</b>
➖➖➖➖➖➖➖➖➖➖

<b>1. Анонимность.</b>
Мы — могила. Никто не узнает, что ты тут был. Твои данные под защитой, как золото в сейфе.

<b>2. Без Антиплагиата.</b>
Мы не льём работы в сеть и не сливаем в системы проверки. Ты — первый и единственный владелец.

<b>3. Честность.</b>
Утром стулья — вечером деньги. Оплата 50/50: половина сразу, половина по готовности.

<b>4. Гарантия.</b>
30 дней на бесплатные правки. Если что-то не так — исправим без лишних вопросов.

<b>5. Сроки.</b>
Дедлайн — закон. Если мы взялись, значит сделаем вовремя.

➖➖➖➖➖➖➖➖➖➖
<i>🤝 Пожал руку — держи слово. Таков закон Дикого Запада.</i>"""

    keyboard = get_back_kb(callback_data="main_menu")

    # Отправляем фото или редактируем текст
    if RULES_IMAGE.exists():
        photo = FSInputFile(RULES_IMAGE)

        # Удаляем старое сообщение и отправляем новое с фото
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        # Fallback: редактируем caption если есть фото
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
