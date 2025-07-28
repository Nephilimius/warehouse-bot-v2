#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для автоматического переноса секретов в .env файл
и обновления всех конфигурационных файлов
"""

import os
import json
import shutil
from datetime import datetime


def backup_files():
    """Создает резервные копии файлов"""
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'config.py', 
        'database.py', 
        'ydb_init.py', 
        'requirements.txt',
        'ydb_key.json'
    ]
    
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"✅ Создана резервная копия: {file} -> {backup_dir}/{file}")
    
    print(f"📁 Резервные копии сохранены в папке: {backup_dir}")
    return backup_dir


def create_env_file():
    """Создает .env файл со всеми секретами"""
    
    env_content = '''# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=7811876172:AAGCf8OIvaUahvP4VuR2m5aWQ5xyQHLoCjI

# Yandex Cloud YDB Configuration
YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
YDB_DATABASE=/ru-central1/b1graibgsi8fsqjbu4v5/etna3daitvujf5j1p5ll
YDB_KEY_FILE=ydb_key.json

# Webhook Configuration
WEBHOOK_PORT=8080

# Admin Users (comma-separated IDs)
ADMIN_USERS=398232017,1014841100

# Environment
ENVIRONMENT=production
DEBUG=False
'''
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Создан файл .env с секретами")


def create_gitignore():
    """Создает/обновляет .gitignore"""
    
    gitignore_content = '''# Environment variables
.env
.env.local
.env.production

# YDB Key
ydb_key.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Backup files
backup_*/

# ngrok
ngrok
ngrok.exe
'''
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("✅ Создан/обновлен файл .gitignore")


def update_config_py():
    """Обновляет config.py для работы с .env"""
    
    config_content = '''# config.py - Конфигурация и константы бота

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
        print("\\n".join(errors))
        raise ValueError("Ошибки в конфигурации!")
    
    print("✅ Конфигурация валидна")
    print(f"🤖 Бот: {TOKEN[:10]}...")
    print(f"💾 База: {YDB_DATABASE}")
    print(f"👑 Админы: {len(ADMINS)} пользователей")
    print(f"🌍 Среда: {ENVIRONMENT}")

if __name__ == "__main__":
    validate_config()
'''
    
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ Обновлен config.py для работы с .env")


def update_database_py():
    """Обновляет database.py для работы с .env"""
    
    # Читаем существующий файл
    with open('database.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем импорты в начале файла
    old_imports = '''# database.py - Функции работы с базой данных YDB

import uuid
import ydb
import ydb.iam
from datetime import datetime
from config import YDB_ENDPOINT, YDB_DATABASE, YDB_KEY_FILE, ADMINS'''
    
    new_imports = '''# database.py - Функции работы с базой данных YDB

import uuid
import ydb
import ydb.iam
from datetime import datetime
from config import YDB_ENDPOINT, YDB_DATABASE, YDB_KEY_FILE, ADMINS'''
    
    # В данном случае imports уже корректные, просто перезаписываем файл
    with open('database.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ database.py готов для работы с .env")


def update_ydb_init_py():
    """Обновляет ydb_init.py для работы с .env"""
    
    ydb_init_content = '''import uuid
from datetime import datetime, timedelta
import ydb
import ydb.iam
from dotenv import load_dotenv
import os

# Загружаем переменные окружения
load_dotenv()

# Константы подключения из .env
YDB_ENDPOINT = os.getenv('YDB_ENDPOINT')
YDB_DATABASE = os.getenv('YDB_DATABASE')
YDB_KEY_FILE = os.getenv('YDB_KEY_FILE', 'ydb_key.json')

if not YDB_ENDPOINT or not YDB_DATABASE:
    raise ValueError("❌ YDB настройки не найдены в .env файле!")

if not os.path.exists(YDB_KEY_FILE):
    raise FileNotFoundError(f"❌ Файл ключа {YDB_KEY_FILE} не найден!")


def get_ydb_connection():
    """Получить подключение к YDB."""
    try:
        credentials = ydb.iam.ServiceAccountCredentials.from_file(YDB_KEY_FILE)
        driver = ydb.Driver(endpoint=YDB_ENDPOINT, database=YDB_DATABASE, credentials=credentials)
        driver.wait(timeout=30)
        pool = ydb.SessionPool(driver)
        return pool, driver
    except Exception as e:
        print(f"❌ Ошибка подключения к YDB: {e}")
        return None, None


def create_tables(pool):
    """Создать все необходимые таблицы."""
    
    def execute(session):
        try:
            # Список SQL запросов для создания таблиц
            tables_queries = [
                """
                CREATE TABLE Users (
                    telegram_id String NOT NULL,
                    username String,
                    role String,
                    tasks_count Int32,
                    average_rating Double,
                    quality_score Double,
                    notifications_enabled Bool DEFAULT true,
                    created_at Timestamp DEFAULT CurrentUtcTimestamp(),
                    PRIMARY KEY (telegram_id)
                );
                """,
                """
                CREATE TABLE Tasks (
                    id String NOT NULL,
                    type String,
                    when_ String,
                    status String,
                    description String,
                    assigned_to String,
                    rating Int32,
                    time_spent Int32,
                    photo_file_id String,
                    created_by String,
                    created_at Timestamp DEFAULT CurrentUtcTimestamp(),
                    completed_at Timestamp,
                    PRIMARY KEY (id)
                );
                """,
                """
                CREATE TABLE Schedule (
                    id String NOT NULL,
                    user_id String,
                    date Date,
                    type String,
                    start_time String,
                    end_time String,
                    status String DEFAULT 'Активно',
                    created_by String,
                    created_at Timestamp DEFAULT CurrentUtcTimestamp(),
                    PRIMARY KEY (id)
                );
                """,
                """
                CREATE TABLE Notifications (
                    id String NOT NULL,
                    user_id String,
                    title String,
                    message String,
                    type String,
                    is_read Bool DEFAULT false,
                    created_at Timestamp DEFAULT CurrentUtcTimestamp(),
                    scheduled_for Timestamp,
                    sent_at Timestamp,
                    PRIMARY KEY (id)
                );
                """,
                """
                CREATE TABLE NotificationSettings (
                    user_id String NOT NULL,
                    general_notifications Bool DEFAULT true,
                    task_reminders Bool DEFAULT true,
                    schedule_updates Bool DEFAULT true,
                    rating_notifications Bool DEFAULT true,
                    reminder_minutes_before Int32 DEFAULT 30,
                    work_hours_start String DEFAULT '09:00',
                    work_hours_end String DEFAULT '18:00',
                    PRIMARY KEY (user_id)
                );
                """,
                """
                CREATE TABLE WorkSchedule (
                    id String NOT NULL,
                    user_id String,
                    day_of_week Int32,
                    start_time String,
                    end_time String,
                    is_active Bool DEFAULT true,
                    created_by String,
                    updated_at Timestamp DEFAULT CurrentUtcTimestamp(),
                    PRIMARY KEY (id)
                );
                """,
                """
                CREATE TABLE TaskTypes (
                    id String NOT NULL,
                    name String,
                    category String,
                    default_duration Int32,
                    requires_photo Bool DEFAULT false,
                    description String,
                    PRIMARY KEY (id)
                );
                """,
                """
                CREATE TABLE Reports (
                    id String NOT NULL,
                    user_id String,
                    report_type String,
                    category String,
                    date_from Date,
                    date_to Date,
                    tasks_completed Int32,
                    average_rating Double,
                    average_time Int32,
                    quality_score Double,
                    delays_count Int32,
                    generated_at Timestamp DEFAULT CurrentUtcTimestamp(),
                    PRIMARY KEY (id)
                );
                """
            ]
            
            # Выполняем создание таблиц
            for i, query in enumerate(tables_queries):
                try:
                    session.transaction().execute(query, commit_tx=True)
                    print(f"✅ Таблица {i+1}/{len(tables_queries)} создана успешно")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"⚠️  Таблица {i+1}/{len(tables_queries)} уже существует")
                    else:
                        print(f"❌ Ошибка создания таблицы {i+1}: {e}")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка выполнения запросов: {e}")
            return False
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False


def create_indexes(pool):
    """Создать индексы для оптимизации."""
    
    def execute(session):
        try:
            indexes = [
                "CREATE INDEX idx_tasks_assigned_to ON Tasks (assigned_to);",
                "CREATE INDEX idx_tasks_status ON Tasks (status);",
                "CREATE INDEX idx_tasks_type ON Tasks (type);",
                "CREATE INDEX idx_schedule_user_date ON Schedule (user_id, date);",
                "CREATE INDEX idx_notifications_user_id ON Notifications (user_id);",
                "CREATE INDEX idx_notifications_scheduled ON Notifications (scheduled_for);",
                "CREATE INDEX idx_work_schedule_user ON WorkSchedule (user_id);",
            ]
            
            for i, index_query in enumerate(indexes):
                try:
                    session.transaction().execute(index_query, commit_tx=True)
                    print(f"✅ Индекс {i+1}/{len(indexes)} создан")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"⚠️  Индекс {i+1}/{len(indexes)} уже существует")
                    else:
                        print(f"❌ Ошибка создания индекса {i+1}: {e}")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка создания индексов: {e}")
            return False
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"❌ Ошибка создания индексов: {e}")
        return False


def insert_test_data(pool):
    """Вставить тестовые данные."""
    
    def execute(session):
        try:
            # Добавляем типы задач
            task_types = [
                ("meal_1", "Обед 1 смена", "Обеды", 60, False, "Обеспечение обеда для первой смены"),
                ("meal_2", "Обед 2 смена", "Обеды", 60, False, "Обеспечение обеда для второй смены"),
                ("cleaning_floors", "Уборка полов", "Уборка", 45, True, "Влажная уборка всех полов в здании"),
                ("cleaning_tables", "Уборка столов", "Уборка", 30, True, "Уборка и дезинфекция рабочих столов"),
                ("cleaning_bathrooms", "Уборка санузлов", "Уборка", 40, True, "Уборка и дезинфекция санузлов"),
                ("recount", "Пересчет", "Пересчеты", 0, False, "Пересчет товара и материалов в течение дня"),
            ]
            
            for task_type in task_types:
                task_type_id = str(uuid.uuid4())
                insert_query = """
                    UPSERT INTO TaskTypes 
                    (id, name, category, default_duration, requires_photo, description)
                    VALUES ("{}", "{}", "{}", {}, {}, "{}")
                """.format(
                    task_type_id, task_type[1], task_type[2], 
                    task_type[3], task_type[4], task_type[5]
                )
                
                session.transaction().execute(insert_query, commit_tx=True)
            
            print("✅ Тестовые типы задач добавлены")
            
            # Добавляем тестовых пользователей
            test_users = [
                ("123456789", "director", "ДС"),
                ("987654321", "assistant_director", "ЗДС"),
                ("111111111", "warehouse_worker1", "Кладовщик"),
                ("222222222", "warehouse_worker2", "Кладовщик"),
                ("333333333", "warehouse_worker3", "Кладовщик"),
            ]
            
            for user in test_users:
                insert_query = """
                    UPSERT INTO Users 
                    (telegram_id, username, role, tasks_count, 
                     average_rating, quality_score, notifications_enabled)
                    VALUES ("{}", "{}", "{}", {}, {}, {}, {})
                """.format(user[0], user[1], user[2], 0, 0.0, 0.0, True)
                
                session.transaction().execute(insert_query, commit_tx=True)
                
                # Добавляем настройки уведомлений для каждого пользователя
                notif_settings_query = """
                    UPSERT INTO NotificationSettings 
                    (user_id, general_notifications, task_reminders, 
                     schedule_updates, rating_notifications)
                    VALUES ("{}", {}, {}, {}, {})
                """.format(user[0], True, True, True, True)
                
                session.transaction().execute(notif_settings_query, commit_tx=True)
            
            print("✅ Тестовые пользователи добавлены")
            
            # Добавляем тестовое расписание
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            schedule_items = [
                ("111111111", tomorrow, "Обеды", "12:00", "13:00"),
                ("222222222", tomorrow, "Обеды", "18:00", "19:00"),
                ("333333333", tomorrow, "Уборка", "09:00", "10:00"),
                ("111111111", tomorrow, "Пересчеты", "14:00", "16:00"),
            ]
            
            for schedule in schedule_items:
                schedule_id = str(uuid.uuid4())
                insert_query = """
                    UPSERT INTO Schedule 
                    (id, user_id, date, type, start_time, end_time, created_by)
                    VALUES ("{}", "{}", Date("{}"), "{}", "{}", "{}", "{}")
                """.format(
                    schedule_id, schedule[0], schedule[1], 
                    schedule[2], schedule[3], schedule[4], "123456789"
                )
                
                session.transaction().execute(insert_query, commit_tx=True)
            
            print("✅ Тестовое расписание добавлено")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка добавления тестовых данных: {e}")
            return False
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"❌ Ошибка вставки тестовых данных: {e}")
        return False


def main():
    """Главная функция инициализации."""
    print("🚀 Начинаем инициализацию базы данных YDB...")
    print(f"🔗 Подключение: {YDB_ENDPOINT}")
    print(f"💾 База данных: {YDB_DATABASE}")
    print(f"🔑 Ключ: {YDB_KEY_FILE}")
    
    # Подключаемся к YDB
    pool, driver = get_ydb_connection()
    if not pool:
        print("❌ Не удалось подключиться к YDB")
        return
    
    try:
        # Создаем таблицы
        print("\\n📋 Создание таблиц...")
        if create_tables(pool):
            print("✅ Все таблицы созданы успешно")
        else:
            print("❌ Ошибка при создании таблиц")
            return
        
        # Создаем индексы
        print("\\n🔍 Создание индексов...")
        if create_indexes(pool):
            print("✅ Все индексы созданы успешно")
        else:
            print("⚠️  Ошибка при создании индексов, продолжаем...")
        
        # Добавляем тестовые данные
        print("\\n📊 Добавление тестовых данных...")
        if insert_test_data(pool):
            print("✅ Тестовые данные добавлены успешно")
        else:
            print("❌ Ошибка при добавлении тестовых данных")
        
        print("\\n🎉 Инициализация базы данных завершена!")
        print("\\n📝 Тестовые пользователи:")
        print("- director (telegram_id: 123456789) - ДС")
        print("- assistant_director (telegram_id: 987654321) - ЗДС")
        print("- warehouse_worker1 (telegram_id: 111111111) - Кладовщик")
        print("- warehouse_worker2 (telegram_id: 222222222) - Кладовщик")
        print("- warehouse_worker3 (telegram_id: 333333333) - Кладовщик")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
    finally:
        if driver:
            driver.stop()


if __name__ == '__main__':
    main()
'''
    
    with open('ydb_init.py', 'w', encoding='utf-8') as f:
        f.write(ydb_init_content)
    
    print("✅ Обновлен ydb_init.py для работы с .env")


def update_requirements():
    """Обновляет requirements.txt"""
    
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем python-dotenv если его нет
    if 'python-dotenv' not in content:
        content += '\npython-dotenv==1.0.0\n'
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Добавлен python-dotenv в requirements.txt")


def create_env_example():
    """Создает .env.example для примера"""
    
    env_example_content = '''# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Yandex Cloud YDB Configuration
YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
YDB_DATABASE=/ru-central1/YOUR_FOLDER_ID/YOUR_DATABASE_ID
YDB_KEY_FILE=ydb_key.json

# Webhook Configuration
WEBHOOK_PORT=8080

# Admin Users (comma-separated IDs)
ADMIN_USERS=123456789,987654321

# Environment
ENVIRONMENT=production
DEBUG=False
'''
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_example_content)
    
    print("✅ Создан файл .env.example для примера")


def main():
    """Главная функция миграции"""
    
    print("🚀 НАЧИНАЕМ МИГРАЦИЮ СЕКРЕТОВ В .ENV")
    print("=" * 50)
    
    try:
        # 1. Создаем резервные копии
        print("\\n📁 Шаг 1: Создание резервных копий...")
        backup_dir = backup_files()
        
        # 2. Создаем .env файл
        print("\\n🔐 Шаг 2: Создание .env файла...")
        create_env_file()
        
        # 3. Создаем/обновляем .gitignore
        print("\\n🚫 Шаг 3: Обновление .gitignore...")
        create_gitignore()
        
        # 4. Обновляем config.py
        print("\\n⚙️  Шаг 4: Обновление config.py...")
        update_config_py()
        
        # 5. Обновляем database.py
        print("\\n💾 Шаг 5: Обновление database.py...")
        update_database_py()
        
        # 6. Обновляем ydb_init.py
        print("\\n🔧 Шаг 6: Обновление ydb_init.py...")
        update_ydb_init_py()
        
        # 7. Обновляем requirements.txt
        print("\\n📦 Шаг 7: Обновление requirements.txt...")
        update_requirements()
        
        # 8. Создаем .env.example
        print("\\n📄 Шаг 8: Создание .env.example...")
        create_env_example()
        
        print("\\n" + "=" * 50)
        print("🎉 МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 50)
        
        print("\\n✅ Что было сделано:")
        print("• Созданы резервные копии всех файлов")
        print("• Создан .env файл со всеми секретами")
        print("• Обновлен .gitignore для защиты секретов")
        print("• Обновлен config.py для работы с .env")
        print("• Обновлен database.py")
        print("• Обновлен ydb_init.py")
        print("• Добавлен python-dotenv в requirements.txt")
        print("• Создан .env.example для примера")
        
        print("\\n🔒 ВАЖНО:")
        print("• .env файл содержит все секреты и НЕ попадет в git")
        print("• ydb_key.json теперь тоже защищен .gitignore")
        print("• Проверьте .env файл перед деплоем")
        print("• При развертывании создайте .env на сервере")
        
        print("\\n📋 Следующие шаги:")
        print("1. Установите python-dotenv: pip install python-dotenv")
        print("2. Проверьте работу: python config.py")
        print("3. Протестируйте бота: python bot_modular.py")
        
        print(f"\\n💾 Резервные копии: {backup_dir}")
        
    except Exception as e:
        print(f"\\n❌ ОШИБКА МИГРАЦИИ: {e}")
        print("Проверьте права доступа к файлам и повторите попытку")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🚀 Готово! Теперь можно безопасно деплоить в Yandex Cloud!")
    else:
        print("\\n💥 Что-то пошло не так, проверьте ошибки выше")