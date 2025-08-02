"""
config.py - Конфигурация для Yandex Cloud Functions

Содержит все настройки и константы для работы Telegram бота
в среде Yandex Cloud Functions с базой данных YDB.
"""

import os

# Токен бота (из переменных окружения Cloud Functions)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")

# Настройки YDB (из переменных окружения)
YDB_ENDPOINT = os.environ.get('YDB_ENDPOINT')
YDB_DATABASE = os.environ.get('YDB_DATABASE')
YDB_SERVICE_ACCOUNT_KEY = os.environ.get('YDB_SERVICE_ACCOUNT_KEY')  # JSON как строка

if not YDB_ENDPOINT or not YDB_DATABASE:
    raise ValueError("❌ YDB настройки не найдены в переменных окружения!")

# Администраторы
admin_users_str = os.environ.get('ADMIN_USERS', '398232017,1014841100')
ADMINS = [int(user_id.strip()) for user_id in admin_users_str.split(',') if user_id.strip()]

# States для ConversationHandler
SEARCH, TASKS_MENU, SCHEDULE_MENU, REPORTS_MENU, NOTIF_MENU, PROFILE = range(6)
ADMIN_MENU, CHANGE_ROLE, DELETE_USER = range(7, 10)
USER_SEARCH = 11

# Дополнительные состояния для расписания
(SCHEDULE_MENU_ADMIN, SCHEDULE_VIEW, SCHEDULE_ADD, 
 SCHEDULE_EDIT, SCHEDULE_DELETE) = range(12, 17)
(ADD_SCHEDULE_TYPE, ADD_SCHEDULE_USER, 
 ADD_SCHEDULE_DATE, ADD_SCHEDULE_TIME) = range(17, 21)
(EDIT_SCHEDULE_SELECT, EDIT_SCHEDULE_FIELD, 
 EDIT_SCHEDULE_VALUE) = range(21, 24)

# Состояния для создания заданий
(CREATE_TASK_TYPE, CREATE_TASK_USER, CREATE_TASK_TIME, 
 CREATE_TASK_DESC, CREATE_TASK_SHELVES) = range(50, 55)

# Новые состояния для управления расписанием
(SCHEDULE_SELECT_TYPE, SCHEDULE_SELECT_USER, SCHEDULE_INPUT_DATE, 
 SCHEDULE_INPUT_TIME, SCHEDULE_INPUT_DETAILS, SCHEDULE_CONFIRM) = range(100, 106)

# Временные слоты для задач
TIME_SLOTS = {
    "В течение дня": "00:00-23:59",
    "09:00-12:00": "09:00-12:00",
    "12:00-15:00": "12:00-15:00",
    "15:00-18:00": "15:00-18:00",
    "18:00-21:00": "18:00-21:00"
}

# Типы задач
TASK_TYPES = {
    "Обеды": "🍽️",
    "Уборка": "🧹",
    "Пересчеты": "🔢"
}

# Эмодзи для ролей
ROLE_EMOJI = {
    "ДС": "👑",
    "ЗДС": "🎖️",
    "Кладовщик": "👷"
}

# Статусы задач
TASK_STATUS = {
    "Ожидающее": "⏳",
    "В работе": "🔄",
    "Выполнено": "✅"
}