# config.py - Конфигурация и константы бота

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токен бота
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")

# Настройки YDB
YDB_ENDPOINT = os.getenv('YDB_ENDPOINT')
YDB_DATABASE = os.getenv('YDB_DATABASE')
YDB_KEY_FILE = os.getenv('YDB_KEY_FILE', 'ydb_key.json')

if not YDB_ENDPOINT or not YDB_DATABASE:
    raise ValueError("❌ YDB настройки не найдены в .env файле!")

# Webhook настройки
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 8080))

# Список администраторов (загружаем из .env)
admin_users_str = os.getenv('ADMIN_USERS', '398232017,1014841100')
ADMINS = [int(user_id.strip()) for user_id in admin_users_str.split(',') if user_id.strip()]

# Режим отладки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# States для ConversationHandler
SEARCH, TASKS_MENU, SCHEDULE_MENU, REPORTS_MENU, NOTIF_MENU, PROFILE = range(6)
ADMIN_MENU, CHANGE_ROLE, DELETE_USER = range(7, 10)
USER_SEARCH = 11

# Дополнительные состояния для расписания
SCHEDULE_MENU_ADMIN, SCHEDULE_VIEW, SCHEDULE_ADD, SCHEDULE_EDIT, SCHEDULE_DELETE = range(12, 17)
ADD_SCHEDULE_TYPE, ADD_SCHEDULE_USER, ADD_SCHEDULE_DATE, ADD_SCHEDULE_TIME = range(17, 21)
EDIT_SCHEDULE_SELECT, EDIT_SCHEDULE_FIELD, EDIT_SCHEDULE_VALUE = range(21, 24)

# Состояния для создания заданий
CREATE_TASK_TYPE, CREATE_TASK_USER, CREATE_TASK_TIME, CREATE_TASK_DESC, CREATE_TASK_SHELVES = range(50, 55)

# Новые состояния для управления расписанием с текстовым вводом
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

# Валидация конфигурации
def validate_config():
    """Проверяет корректность конфигурации"""
    errors = []
    
    if not TOKEN:
        errors.append("❌ TELEGRAM_BOT_TOKEN не установлен")
    
    if not YDB_ENDPOINT:
        errors.append("❌ YDB_ENDPOINT не установлен")
        
    if not YDB_DATABASE:
        errors.append("❌ YDB_DATABASE не установлен")
        
    if not os.path.exists(YDB_KEY_FILE):
        errors.append(f"❌ Файл {YDB_KEY_FILE} не найден")
    
    if not ADMINS:
        errors.append("❌ ADMIN_USERS не настроены")
    
    if errors:
        print("\n".join(errors))
        raise ValueError("Ошибки в конфигурации!")
    
    print("✅ Конфигурация валидна")
    print(f"🤖 Бот: {TOKEN[:10]}...")
    print(f"💾 База: {YDB_DATABASE}")
    print(f"👑 Админы: {len(ADMINS)} пользователей")
    print(f"🌍 Среда: {ENVIRONMENT}")

if __name__ == "__main__":
    validate_config()
