"""
Хендлер главного меню
Возврат в главное меню из любого раздела
"""

from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from bot.keyboards.inline import get_main_menu_kb

router = Router(name="menu")

# Путь к изображению главного меню
ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"
MAIN_MENU_IMAGE = ASSETS_DIR / "main_menu.jpg"

# Текст главного меню (дублируем из start.py для консистентности)
MAIN_MENU_CAPTION = """🤠 <b>Йо-хо, Ковбой! Добро пожаловать в Академический Салун!</b>

Здесь мы решаем учебные вопросы без лишней суеты.
С тебя — задача, с нас — готовая работа и спокойный сон.

<b>Мы гарантируем:</b>
🛡 <b>Безопасность</b> (не сливаем в антиплагиат)
⚡️ <b>Скорость</b> (от 24 часов)
💰 <b>Честность</b> (оплата частями)

<i>Чего изволишь? Выбирай в меню:</i> 👇"""


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery) -> None:
    """
    Возврат в главное меню
    """
    await callback.answer()

    keyboard = get_main_menu_kb()

    # Отправляем главное меню с фото
    if MAIN_MENU_IMAGE.exists():
        photo = FSInputFile(MAIN_MENU_IMAGE)

        # Удаляем старое сообщение и отправляем новое
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo,
            caption=MAIN_MENU_CAPTION,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        # Fallback без фото
        try:
            await callback.message.edit_caption(
                caption=MAIN_MENU_CAPTION,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except Exception:
            await callback.message.delete()
            await callback.message.answer(
                text=MAIN_MENU_CAPTION,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
