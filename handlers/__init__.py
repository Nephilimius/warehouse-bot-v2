"""
Модуль хендлеров для Telegram бота
Содержит все обработчики команд и callback'ов
"""

from .main_handlers import *
from .admin_handlers import *
from .task_handlers import *
from .notification_handlers import *
from .report_handlers import *
from .callback_router import *

__all__ = [
    'handle_start_command',
    'handle_text_message', 
    'handle_callback_query',
    'handle_admin_functions',
    'handle_task_operations',
    'handle_notifications',
    'handle_reports'
]
