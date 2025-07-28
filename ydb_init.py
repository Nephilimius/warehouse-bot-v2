import uuid
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
        print("\n📋 Создание таблиц...")
        if create_tables(pool):
            print("✅ Все таблицы созданы успешно")
        else:
            print("❌ Ошибка при создании таблиц")
            return
        
        # Создаем индексы
        print("\n🔍 Создание индексов...")
        if create_indexes(pool):
            print("✅ Все индексы созданы успешно")
        else:
            print("⚠️  Ошибка при создании индексов, продолжаем...")
        
        # Добавляем тестовые данные
        print("\n📊 Добавление тестовых данных...")
        if insert_test_data(pool):
            print("✅ Тестовые данные добавлены успешно")
        else:
            print("❌ Ошибка при добавлении тестовых данных")
        
        print("\n🎉 Инициализация базы данных завершена!")
        print("\n📝 Тестовые пользователи:")
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
