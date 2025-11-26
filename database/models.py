"""
SQLAlchemy модели базы данных
Enterprise CRM Schema
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


class User(Base):
    """
    Модель пользователя (ковбоя салуна)
    Enterprise CRM User Schema
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Баланс пользователя
    balance: Mapped[int] = mapped_column(Integer, default=0)

    # Реферальная система
    referrer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # CRM Группа статусов: guest, client, vip, banned
    status_group: Mapped[str] = mapped_column(String(50), default="guest")

    # Юридическая оферта
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    # CRM заметки админа
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Отслеживание активности (для retention)
    last_active: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

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
    orders: Mapped[list["Order"]] = relationship(back_populates="user", lazy="selectin")

    # Связь с транзакциями
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.telegram_id} ({self.first_name})>"

    @property
    def display_name(self) -> str:
        """Отображаемое имя пользователя"""
        if self.username:
            return f"@{self.username}"
        return self.first_name

    @property
    def magic_link(self) -> str:
        """Magic Link для Telegram (кликабельный в логах)"""
        return f"tg://user?id={self.telegram_id}"

    @property
    def status_emoji(self) -> str:
        """Эмодзи для статуса группы"""
        emojis = {
            "guest": "👤",
            "client": "🤠",
            "vip": "⭐",
            "banned": "🚫",
        }
        return emojis.get(self.status_group, "👤")


class Order(Base):
    """
    Модель заказа
    Enterprise CRM Order Schema
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Связь с пользователем
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship(back_populates="orders")

    # Данные заказа
    subject: Mapped[str] = mapped_column(String(500))  # Предмет и тема
    work_type: Mapped[str] = mapped_column(String(100))  # type_coursework, type_diploma, etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Подробное описание

    # Файлы от пользователя (JSON строка с массивом файлов)
    files_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статус заказа: pending, pricing, payment_wait, working, review, ready, completed, canceled
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)

    # Цена (устанавливается админом)
    price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Дедлайн
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Комментарий от админа (внутренний)
    admin_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Legacy поля для обратной совместимости
    work_type_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deadline_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    final_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    final_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    paid_amount: Mapped[int] = mapped_column(Integer, default=0)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        """Получить список file_id (legacy)"""
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
            "pending": "🆕",
            "pricing": "💭",
            "payment_wait": "⏳",
            "working": "🔄",
            "review": "👀",
            "ready": "📦",
            "completed": "✅",
            "canceled": "❌",
            # Legacy статусы
            "new": "🆕",
            "pending_payment": "⏳",
            "paid": "💰",
            "in_progress": "🔄",
            "cancelled": "❌",
        }
        return emojis.get(self.status, "📋")

    @property
    def status_name(self) -> str:
        """Название статуса на русском"""
        names = {
            "pending": "Новый",
            "pricing": "Оценка",
            "payment_wait": "Ожидает оплаты",
            "working": "В работе",
            "review": "На проверке",
            "ready": "Готов к выдаче",
            "completed": "Завершён",
            "canceled": "Отменён",
            # Legacy статусы
            "new": "Новый",
            "pending_payment": "Ожидает оплаты",
            "paid": "Оплачен",
            "in_progress": "В работе",
            "cancelled": "Отменён",
        }
        return names.get(self.status, self.status)


class Transaction(Base):
    """
    Модель транзакции (движение средств)
    Enterprise CRM Transaction Schema
    """

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Связь с пользователем
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship(back_populates="transactions")

    # Сумма: положительная для пополнения, отрицательная для списания
    amount: Mapped[int] = mapped_column(Integer)

    # Тип транзакции: deposit, payment, refund, bonus
    type: Mapped[str] = mapped_column(String(50), index=True)

    # Описание транзакции
    description: Mapped[str] = mapped_column(String(500))

    # Связь с заказом (опционально)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"), nullable=True)

    # Временная метка
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Transaction #{self.id} ({self.type}: {self.amount})>"

    @property
    def type_emoji(self) -> str:
        """Эмодзи для типа транзакции"""
        emojis = {
            "deposit": "💵",
            "payment": "💸",
            "refund": "↩️",
            "bonus": "🎁",
        }
        return emojis.get(self.type, "💰")

    @property
    def type_name(self) -> str:
        """Название типа на русском"""
        names = {
            "deposit": "Пополнение",
            "payment": "Оплата",
            "refund": "Возврат",
            "bonus": "Бонус",
        }
        return names.get(self.type, self.type)

    @property
    def formatted_amount(self) -> str:
        """Форматированная сумма со знаком"""
        if self.amount >= 0:
            return f"+{self.amount} ₽"
        return f"{self.amount} ₽"
