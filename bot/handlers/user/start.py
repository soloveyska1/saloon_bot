"""
Хендлер команды /start
Первое знакомство ковбоя с салуном
"""

from pathlib import Path

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

from bot.keyboards.inline import get_main_menu_kb

router = Router(name="start")

# Путь к изображению главного меню
ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"
MAIN_MENU_IMAGE = ASSETS_DIR / "main_menu.jpg"


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Обработка команды /start
    Приветствие нового посетителя салуна с фото
    """

    caption = """🤠 <b>Йо-хо, Ковбой! Добро пожаловать в Академический Салун!</b>

Здесь мы решаем учебные вопросы без лишней суеты.
С тебя — задача, с нас — готовая работа и спокойный сон.

<b>Мы гарантируем:</b>
🛡 <b>Безопасность</b> (не сливаем в антиплагиат)
⚡️ <b>Скорость</b> (от 24 часов)
💰 <b>Честность</b> (оплата частями)

<i>Чего изволишь? Выбирай в меню:</i> 👇"""

    # Отправляем фото с подписью и inline-клавиатурой
    if MAIN_MENU_IMAGE.exists():
        photo = FSInputFile(MAIN_MENU_IMAGE)
        await message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_main_menu_kb(),
        )
    else:
        # Fallback: если изображения нет, отправляем только текст
        await message.answer(
            text=caption,
            parse_mode="HTML",
            reply_markup=get_main_menu_kb(),
        )
