# config.py - Универсальная конфигурация для локальной разработки и Yandex Cloud Functions

import os

# Определяем среду выполнения
IS_CLOUD_FUNCTIONS = bool(os.environ.get('_HANDLER'))  # В Cloud Functions всегда есть _HANDLER

if not IS_CLOUD_FUNCTIONS:
    # Локальная разработка - пытаемся загрузить .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Локальная разработка: .env файл загружен")
    except ImportError:
        print("⚠️  python-dotenv не найден, используем системные переменные")
    except Exception as e:
        print(f"⚠️  Ошибка загрузки .env: {e}")
else:
    print("✅ Cloud Functions: используем переменные окружения")

# Токен бота (из переменных окружения)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('TELEGRAM_BOT')
if not TOKEN:
    available_vars = [k for k in os.environ.keys() if 'BOT' in k or 'TELEGRAM' in k]
    print(f"❌ Токен не найден. Доступные переменные с BOT/TELEGRAM: {available_vars}")
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")

# Настройки YDB
YDB_ENDPOINT = os.environ.get('YDB_ENDPOINT') or os.environ.get('YDB_ENDPOIN')  # На случай опечатки
YDB_DATABASE = os.environ.get('YDB_DATABASE') or os.environ.get('YDB_DATABAS')  # На случай опечатки
YDB_SERVICE_ACCOUNT_KEY = os.environ.get('YDB_SERVICE_ACCOUNT_KEY')  # JSON как строка для Cloud Functions
YDB_KEY_FILE = os.environ.get('YDB_KEY_FILE')  # Путь к файлу для локальной разработки

# Проверяем YDB настройки
if not YDB_ENDPOINT or not YDB_DATABASE:
    available_ydb_vars = [k for k in os.environ.keys() if 'YDB' in k]
    print(f"⚠️  YDB переменные: {available_ydb_vars}")
    if IS_CLOUD_FUNCTIONS:
        print("❌ В Cloud Functions YDB настройки обязательны!")
        raise ValueError("❌ YDB настройки не найдены в переменных окружения!")
    else:
        print("⚠️  YDB не настроена - некоторые функции будут недоступны")

# Администраторы
admin_users_str = os.environ.get('ADMIN_USERS', '398232017,1014841100')
try:
    ADMINS = [int(user_id.strip()) for user_id in admin_users_str.split(',') if user_id.strip()]
    print(f"✅ Админы: {len(ADMINS)} пользователей")
except Exception as e:
    print(f"⚠️  Ошибка парсинга ADMIN_USERS: {e}")
    ADMINS = [398232017, 1014841100]  # Fallback

# Отладочная информация
print(f"🔧 Режим: {'Cloud Functions' if IS_CLOUD_FUNCTIONS else 'Локальная разработка'}")
print(f"🔑 Токен: {'✅ Найден' if TOKEN else '❌ Не найден'}")
print(f"🗄️  YDB: {'✅ Настроена' if YDB_ENDPOINT and YDB_DATABASE else '❌ Не настроена'}")

# States для ConversationHandler (остается без изменений)
SEARCH, TASKS_MENU, SCHEDULE_MENU, REPORTS_MENU, NOTIF_MENU, PROFILE = range(6)
ADMIN_MENU, CHANGE_ROLE, DELETE_USER = range(7, 10)
USER_SEARCH = 11

# Дополнительные состояния для расписания
SCHEDULE_MENU_ADMIN, SCHEDULE_VIEW, SCHEDULE_ADD, SCHEDULE_EDIT, SCHEDULE_DELETE = range(12, 17)
ADD_SCHEDULE_TYPE, ADD_SCHEDULE_USER, ADD_SCHEDULE_DATE, ADD_SCHEDULE_TIME = range(17, 21)
EDIT_SCHEDULE_SELECT, EDIT_SCHEDULE_FIELD, EDIT_SCHEDULE_VALUE = range(21, 24)

# Состояния для создания заданий
CREATE_TASK_TYPE, CREATE_TASK_USER, CREATE_TASK_TIME, CREATE_TASK_DESC, CREATE_TASK_SHELVES = range(50, 55)

# Новые состояния для управления расписанием
SCHEDULE_SELECT_TYPE, SCHEDULE_SELECT_USER, SCHEDULE_INPUT_DATE, SCHEDULE_INPUT_TIME, SCHEDULE_INPUT_DETAILS, SCHEDULE_CONFIRM = range(100, 106)

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