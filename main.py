"""
Академический Салун - Telegram Bot
Точка входа приложения
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database import init_db
from bot.handlers import setup_routers
from bot.middlewares import DatabaseMiddleware, TrackActivityMiddleware, ShadowLogMiddleware


async def on_startup(bot: Bot) -> None:
    """Действия при запуске бота"""
    # Инициализируем базу данных
    await init_db()
    logging.info("База данных инициализирована")

    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logging.info(f"Бот запущен: @{bot_info.username}")


async def on_shutdown(bot: Bot) -> None:
    """Действия при остановке бота"""
    logging.info("Бот остановлен")


async def main() -> None:
    """Главная функция запуска бота"""

    # Настройка логирования
    logging.basicConfig(
        level=logging.DEBUG if config.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    # Проверяем токен
    if not config.bot.token:
        logging.error("BOT_TOKEN не установлен! Проверьте файл .env")
        sys.exit(1)

    # Создаём бота
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Создаём диспетчер
    dp = Dispatcher()

    # Подключаем middleware (порядок важен!)
    # 1. DatabaseMiddleware - инъекция сессии БД и пользователя
    dp.update.middleware(DatabaseMiddleware())
    # 2. TrackActivityMiddleware - отслеживание активности (требует user из DatabaseMiddleware)
    dp.update.middleware(TrackActivityMiddleware())
    # 3. ShadowLogMiddleware - архивирование файлов в лог-канал
    dp.message.middleware(ShadowLogMiddleware())

    # Регистрируем события startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Подключаем роутеры
    dp.include_router(setup_routers())

    # Удаляем webhook и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)

    logging.info("=" * 50)
    logging.info("🤠 АКАДЕМИЧЕСКИЙ САЛУН ОТКРЫВАЕТСЯ!")
    logging.info("=" * 50)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
