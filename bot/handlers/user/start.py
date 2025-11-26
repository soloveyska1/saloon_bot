"""
Хендлер команды /start
Первое знакомство ковбоя с салуном
"""

import logging
from pathlib import Path

from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_main_menu_kb
from database.models import User

router = Router(name="start")
logger = logging.getLogger(__name__)

# Путь к изображению главного меню
ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"
MAIN_MENU_IMAGE = ASSETS_DIR / "main_menu.jpg"


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    user: User,
    session: AsyncSession,
    is_new_user: bool = False,
) -> None:
    """
    Обработка команды /start
    Приветствие нового посетителя салуна с фото
    Поддержка реферальной системы через deep-linking
    """

    # Обработка реферальной системы
    if is_new_user and command.args:
        try:
            referrer_telegram_id = int(command.args)

            # Проверяем, что пользователь не приглашает сам себя
            if referrer_telegram_id != message.from_user.id:
                # Проверяем, существует ли реферер в БД
                stmt = select(User).where(User.telegram_id == referrer_telegram_id)
                result = await session.execute(stmt)
                referrer = result.scalar_one_or_none()

                if referrer:
                    # Записываем referrer_id
                    user.referrer_id = referrer_telegram_id
                    logger.info(
                        f"Пользователь {message.from_user.id} зарегистрирован по реферальной ссылке от {referrer_telegram_id}"
                    )
        except (ValueError, TypeError):
            # Аргумент не является числом — игнорируем
            pass

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
