"""
Middlewares package - промежуточные обработчики
Enterprise CRM Middleware Stack
"""

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.activity import TrackActivityMiddleware
from bot.middlewares.shadow_log import ShadowLogMiddleware

__all__ = [
    "DatabaseMiddleware",
    "TrackActivityMiddleware",
    "ShadowLogMiddleware",
]
