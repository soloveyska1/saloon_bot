"""
Database engine и управление сессиями
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import config

# Создаём асинхронный движок
engine = create_async_engine(
    config.db.url,
    echo=config.db.echo,
)

# Фабрика сессий
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Инициализация базы данных (создание таблиц)"""
    from database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии для работы с БД"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
