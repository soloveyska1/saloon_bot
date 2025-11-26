"""
Конфигурация бота "Академический Салун"
Загрузка переменных окружения и настроек
"""

from dataclasses import dataclass
from os import getenv
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Настройки Telegram бота"""
    token: str
    name: str = "Академический Салун"


@dataclass
class DatabaseConfig:
    """Настройки базы данных"""
    url: str
    echo: bool = False  # Логирование SQL запросов


@dataclass
class Config:
    """Главный конфиг приложения"""
    bot: BotConfig
    db: DatabaseConfig
    admin_ids: list[int]
    debug: bool = False


def load_config() -> Config:
    """Загрузка конфигурации из переменных окружения"""

    # Парсим список админов
    admin_ids_str = getenv("ADMIN_IDS", "")
    admin_ids = [
        int(admin_id.strip())
        for admin_id in admin_ids_str.split(",")
        if admin_id.strip().isdigit()
    ]

    return Config(
        bot=BotConfig(
            token=getenv("BOT_TOKEN", ""),
            name=getenv("BOT_NAME", "Академический Салун"),
        ),
        db=DatabaseConfig(
            url=getenv("DATABASE_URL", "sqlite+aiosqlite:///./database/saloon.db"),
            echo=getenv("DEBUG", "False").lower() == "true",
        ),
        admin_ids=admin_ids,
        debug=getenv("DEBUG", "False").lower() == "true",
    )


# Глобальный экземпляр конфига
config = load_config()
