"""
SQLAlchemy модели базы данных
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


class User(Base):
    """Модель пользователя (ковбоя салуна)"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Ранг в салуне
    rank: Mapped[str] = mapped_column(String(50), default="greenhorn")  # greenhorn, cowboy, sheriff

    # Реферальная система
    referral_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    referred_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    referrer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # ID пригласившего пользователя

    # Бонусы и баланс
    bonus_balance: Mapped[int] = mapped_column(default=0)
    balance: Mapped[int] = mapped_column(Integer, default=0)  # Баланс пользователя

    # Юридическая оферта
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False)  # Флаг принятия оферты

    # CRM заметки
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Заметки админа

    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Связь с заказами
    orders: Mapped[list["Order"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.telegram_id} ({self.first_name})>"


class Order(Base):
    """Модель заказа"""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Связь с пользователем
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship(back_populates="orders")

    # Данные заказа
    work_type: Mapped[str] = mapped_column(String(100))  # type_coursework, type_diploma, etc.
    work_type_name: Mapped[str] = mapped_column(String(255))  # Человекочитаемое название
    subject: Mapped[str] = mapped_column(Text)  # Предмет и тема
    deadline: Mapped[str] = mapped_column(String(50))  # week, medium, urgent
    deadline_name: Mapped[str] = mapped_column(String(100))  # Человекочитаемое название

    # Файлы от пользователя (file_id через запятую)
    file_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Голосовое сообщение (если было)
    voice_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Финальный файл от админа (готовая работа)
    final_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    final_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Статус заказа
    status: Mapped[str] = mapped_column(String(50), default="new")
    # Статусы: new, pending_payment, paid, in_progress, completed, cancelled

    # Цена и оплата
    price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    paid_amount: Mapped[int] = mapped_column(Integer, default=0)

    # Комментарий от пользователя
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Комментарий от админа
    admin_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Order #{self.id} ({self.status})>"

    @property
    def file_ids_list(self) -> list[str]:
        """Получить список file_id"""
        if not self.file_ids:
            return []
        return [fid.strip() for fid in self.file_ids.split(",") if fid.strip()]

    @property
    def files_count(self) -> int:
        """Количество прикреплённых файлов"""
        return len(self.file_ids_list)

    @property
    def status_emoji(self) -> str:
        """Эмодзи для статуса"""
        emojis = {
            "new": "🆕",
            "pending_payment": "⏳",
            "paid": "💰",
            "in_progress": "🔄",
            "completed": "✅",
            "cancelled": "❌",
        }
        return emojis.get(self.status, "📋")

    @property
    def status_name(self) -> str:
        """Название статуса на русском"""
        names = {
            "new": "Новый",
            "pending_payment": "Ожидает оплаты",
            "paid": "Оплачен",
            "in_progress": "В работе",
            "completed": "Готов",
            "cancelled": "Отменён",
        }
        return names.get(self.status, self.status)
