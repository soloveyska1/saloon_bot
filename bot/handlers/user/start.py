"""
Хендлер команды /start
Первое знакомство ковбоя с салуном
"""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Обработка команды /start
    Приветствие нового посетителя салуна
    """
    user_name = message.from_user.first_name if message.from_user else "Незнакомец"

    welcome_text = f"""
🤠 <b>Йо-хо, {user_name}!</b>

Добро пожаловать в <b>Академический Салун</b>, партнёр!

Здесь мы помогаем ковбоям вроде тебя справляться с учебными делами:
📝 Курсовые работы
📚 Дипломы и ВКР
✍️ Рефераты и эссе
📊 Контрольные работы

<i>Присаживайся к барной стойке, и давай обсудим, чем могу помочь!</i>

🌟 Ты сейчас в ранге: <b>Новичок (Greenhorn)</b>
Выполняй заказы — повышай ранг и получай бонусы!
    """

    await message.answer(welcome_text, parse_mode="HTML")
