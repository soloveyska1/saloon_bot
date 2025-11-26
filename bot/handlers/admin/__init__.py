"""
Admin handlers - хендлеры для администраторов
Enterprise CRM Admin Panel
"""

from aiogram import Router

from bot.filters.admin import IsAdmin
from bot.handlers.admin.menu import router as menu_router
from bot.handlers.admin.orders import router as orders_router
from bot.handlers.admin.users import router as users_router
from bot.handlers.admin.broadcast import router as broadcast_router

# Главный роутер админки с фильтром IsAdmin
router = Router(name="admin")

# Применяем фильтр IsAdmin ко всему роутеру
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Подключаем админские хендлеры
router.include_router(menu_router)
router.include_router(orders_router)
router.include_router(users_router)
router.include_router(broadcast_router)
