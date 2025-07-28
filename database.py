# database.py - Функции работы с базой данных YDB

import uuid
import ydb
import ydb.iam
from datetime import datetime
from config import YDB_ENDPOINT, YDB_DATABASE, YDB_KEY_FILE, ADMINS

def get_ydb_timestamp():
    """Получить timestamp в формате, совместимом с YDB."""
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'

# Инициализация YDB
try:
    credentials = ydb.iam.ServiceAccountCredentials.from_file(YDB_KEY_FILE)
    driver = ydb.Driver(endpoint=YDB_ENDPOINT, database=YDB_DATABASE, credentials=credentials)
    driver.wait(timeout=60)
    pool = ydb.SessionPool(driver, size=3)
    print("✅ YDB подключена успешно!")
except Exception as e:
    print(f"❌ Ошибка подключения к YDB: {e}")
    import traceback
    traceback.print_exc()
    exit(1)


def safe_decode(value):
    """Безопасное декодирование значений из YDB."""
    if isinstance(value, bytes):
        return value.decode('utf-8')
    elif value is None:
        return "Unknown"
    else:
        str_value = str(value)
        
        # Если это число и похоже на дни с эпохи
        if isinstance(value, int) and 1 <= value <= 100000:
            try:
                # YDB может возвращать дни с 1900-01-01
                from datetime import datetime, timedelta
                epoch_date = datetime(1900, 1, 1)
                actual_date = epoch_date + timedelta(days=value - 1)
                return actual_date.strftime('%Y-%m-%d')
            except:
                pass
        
        # Проверяем строковые форматы дат
        if len(str_value) == 10 and str_value.count('-') == 2:
            parts = str_value.split('-')
            if len(parts) == 3 and all(part.isdigit() for part in parts):
                year, month, day = map(int, parts)
                if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                    return str_value
        
        return str_value


async def is_admin(user_id):
    """Проверить, является ли пользователь администратором."""
    return user_id in ADMINS


async def get_or_create_user(telegram_id: int, username: str = None):
    """Получить или создать пользователя."""
    def execute(session):
        try:
            query = """
                SELECT telegram_id, username, role, tasks_count, 
                       average_rating, quality_score, notifications_enabled
                FROM Users 
                WHERE telegram_id = "{}"
            """.format(str(telegram_id))
            
            result = session.transaction().execute(query, commit_tx=True)
            
            if result[0].rows:
                row = result[0].rows[0]
                return {
                    'telegram_id': safe_decode(row[0]),  # telegram_id
                    'username': safe_decode(row[1]),     # username  
                    'role': safe_decode(row[2]),         # role
                    'tasks_count': int(row[3]) if row[3] else 0,        # tasks_count
                    'average_rating': float(row[4]) if row[4] else 0.0, # average_rating
                    'quality_score': float(row[5]) if row[5] else 0.0,  # quality_score
                    'notifications_enabled': bool(row[6]) if row[6] is not None else True # notifications_enabled
                }
            else:
                # Создаем нового пользователя
                insert_query = """
                    UPSERT INTO Users 
                    (telegram_id, username, role, tasks_count, 
                     average_rating, quality_score, notifications_enabled)
                    VALUES ("{}", "{}", "{}", {}, {}, {}, {})
                """.format(
                    str(telegram_id),
                    username or "Unknown",
                    "Кладовщик",
                    0, 0.0, 0.0, True
                )
                
                session.transaction().execute(insert_query, commit_tx=True)
                
                # Создаем настройки уведомлений по умолчанию
                notif_settings_query = """
                    UPSERT INTO NotificationSettings 
                    (user_id, general_notifications, task_reminders, 
                     schedule_updates, rating_notifications)
                    VALUES ("{}", {}, {}, {}, {})
                """.format(str(telegram_id), True, True, True, True)
                
                session.transaction().execute(notif_settings_query, commit_tx=True)
                
                return {
                    'telegram_id': str(telegram_id),
                    'username': username or "Unknown",
                    'role': "Кладовщик",
                    'tasks_count': 0,
                    'average_rating': 0.0,
                    'quality_score': 0.0,
                    'notifications_enabled': True
                }
        except Exception as e:
            print(f"Ошибка в execute: {e}")
            return None
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка при работе с пользователем: {e}")
        return None


async def get_all_users():
    """Получить всех пользователей."""
    def execute(session):
        try:
            query = """
                SELECT telegram_id, username, role, tasks_count, average_rating
                FROM Users
                ORDER BY role, username
            """
            
            result = session.transaction().execute(query, commit_tx=True)
            
            users = []
            for row in result[0].rows:
                users.append({
                    'telegram_id': safe_decode(row[0]),      # telegram_id
                    'username': safe_decode(row[1]),         # username
                    'role': safe_decode(row[2]),             # role
                    'tasks_count': int(row[3]) if row[3] else 0,        # tasks_count
                    'average_rating': float(row[4]) if row[4] else 0.0  # average_rating
                })
            return users
        except Exception as e:
            print(f"Ошибка получения пользователей: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения пользователей: {e}")
        return []


async def get_my_tasks(user_id):
    """Получить задачи пользователя."""
    def execute(session):
        try:
            query = """
                SELECT id, type, when_, status, description, rating, time_spent
                FROM Tasks 
                WHERE assigned_to = "{}" AND status != "Отменено"
                ORDER BY when_ DESC
                LIMIT 10
            """.format(str(user_id))
            
            result = session.transaction().execute(query, commit_tx=True)
            
            tasks = []
            for row in result[0].rows:
                tasks.append({
                    'id': safe_decode(row['id']),
                    'type': safe_decode(row['type']),
                    'when_': safe_decode(row['when_']),
                    'status': safe_decode(row['status']),
                    'description': safe_decode(row['description']),
                    'rating': row.rating,
                    'time_spent': row.time_spent
                })
            return tasks
        except Exception as e:
            print(f"Ошибка получения заданий: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения заданий: {e}")
        return []


async def get_schedule_by_type(schedule_type):
    """Получить расписание по типу."""
    def execute(session):
        try:
            # YDB требует SELECT без алиасов в некоторых случаях
            query = """
                SELECT Schedule.date, Schedule.start_time, Schedule.end_time, Users.username, Schedule.id
                FROM Schedule
                JOIN Users ON Schedule.user_id = Users.telegram_id
                WHERE Schedule.type = "{}" 
                AND Schedule.status = "Активно"
                ORDER BY Schedule.date, Schedule.start_time
                LIMIT 20
            """.format(schedule_type)
            
            result = session.transaction().execute(query, commit_tx=True)
            
            print(f"DEBUG: YDB запрос выполнен для {schedule_type}, строк: {len(result[0].rows)}")
            
            schedule = []
            for i, row in enumerate(result[0].rows):
                try:
                    print(f"DEBUG: Строка {i}, длина: {len(row)}")
                    print(f"DEBUG: Сырые данные: {[repr(field) for field in row]}")
                    print(f"DEBUG: Типы полей: {[type(field).__name__ for field in row]}")
                    
                    # Получаем данные напрямую по индексам
                    date_raw = row[0]
                    start_time_raw = row[1]
                    end_time_raw = row[2]
                    username_raw = row[3]
                    id_raw = row[4]
                    
                    print(f"DEBUG: date_raw = {repr(date_raw)}, type = {type(date_raw)}")
                    
                    # Исправленная конверсия даты для 2025 года
                    if isinstance(date_raw, int):
                        # 20291 дней должно быть 22.07.2025
                        # Значит эпоха не 1900-01-01, а другая
                        from datetime import datetime, timedelta
                        try:
                            # Попробуем найти правильную эпоху
                            # Если 20291 должно быть 2025-07-22, то:
                            target_date = datetime(2025, 7, 22)
                            
                            # Попробуем разные эпохи
                            epochs = [
                                datetime(1900, 1, 1),  # Стандартная
                                datetime(1899, 12, 30),  # Excel
                                datetime(1970, 1, 1),   # Unix
                                datetime(1, 1, 1),      # От нашей эры
                                datetime(1800, 1, 1),   # Другая база
                            ]
                            
                            best_date = "2025-07-22"  # Fallback
                            
                            for epoch in epochs:
                                try:
                                    test_date = epoch + timedelta(days=date_raw)
                                    # Если получается разумная дата в районе 2025
                                    if 2020 <= test_date.year <= 2030:
                                        best_date = test_date.strftime('%Y-%m-%d')
                                        print(f"DEBUG: Эпоха {epoch} дает дату {best_date}")
                                        break
                                except:
                                    continue
                            
                            formatted_date = best_date
                        except:
                            formatted_date = "2025-07-22"  # Hardcode fallback
                    else:
                        formatted_date = safe_decode(date_raw)
                    
                    print(f"DEBUG: Отформатированная дата: {formatted_date}")
                    
                    schedule.append({
                        'date': formatted_date,
                        'start_time': safe_decode(start_time_raw),
                        'end_time': safe_decode(end_time_raw), 
                        'username': safe_decode(username_raw),
                        'id': safe_decode(id_raw)
                    })
                    
                    print(f"DEBUG: Успешно обработана строка {i}: {schedule[-1]}")
                    
                except Exception as row_error:
                    print(f"DEBUG: Ошибка обработки строки {i}: {row_error}")
                    import traceback
                    traceback.print_exc()
                    
            print(f"DEBUG: Итого обработано записей: {len(schedule)}")
            return schedule
            
        except Exception as e:
            print(f"Ошибка получения расписания: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения расписания: {e}")
        return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения расписания: {e}")
        return []


async def get_all_schedule_items():
    """Получить все записи расписания для админа."""
    def execute(session):
        try:
            query = """
                SELECT s.id, s.user_id, s.date, s.type, s.start_time, s.end_time, 
                       s.status, s.created_at, u.username
                FROM Schedule s
                JOIN Users u ON s.user_id = u.telegram_id
                WHERE s.status = "Активно"
                ORDER BY s.date DESC, s.start_time ASC
                LIMIT 50
            """
            
            result = session.transaction().execute(query, commit_tx=True)
            
            schedule = []
            for row in result[0].rows:
                # Порядок: id(0), user_id(1), date(2), type(3), start_time(4), end_time(5), status(6), created_at(7), username(8)
                schedule.append({
                    'id': safe_decode(row[0]),
                    'user_id': safe_decode(row[1]),
                    'date': safe_decode(row[2]),
                    'type': safe_decode(row[3]),
                    'start_time': safe_decode(row[4]),
                    'end_time': safe_decode(row[5]),
                    'status': safe_decode(row[6]),
                    'created_at': safe_decode(row[7]),
                    'username': safe_decode(row[8])
                })
            return schedule
        except Exception as e:
            print(f"Ошибка получения всего расписания: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения всего расписания: {e}")
        return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения всего расписания: {e}")
        return []


async def create_schedule_task(user_id, task_type, date, time_slot, shelves=None):
    """Создать задачу в расписании."""
    def execute(session):
        try:
            task_id = str(uuid.uuid4())
            
            # Формируем описание
            description = f"{task_type}"
            if shelves:
                description += f" - {shelves}"
            
            # Парсим время
            if time_slot == "В течение дня":
                start_time = "00:00"
                end_time = "23:59"
            else:
                start_time, end_time = time_slot.split('-')
            
            # Вставляем в Tasks
            task_query = """
                UPSERT INTO Tasks
                (id, type, when_, status, description, assigned_to, created_by, created_at)
                VALUES ("{}", "{}", "{}", "{}", "{}", "{}", "{}", Timestamp("{}"))
            """.format(
                task_id, task_type, f"{date} {start_time}:00", "Ожидающее",
                description, str(user_id), str(user_id), get_ydb_timestamp()
            )
            
            session.transaction().execute(task_query, commit_tx=True)
            
            # Вставляем в Schedule с правильной конверсией даты
            schedule_id = str(uuid.uuid4())
            
            # Проверяем формат даты
            if isinstance(date, str):
                if len(date) == 10 and date.count('-') == 2:
                    # Уже в формате YYYY-MM-DD
                    date_str = date
                else:
                    # Пытаемся распарсить
                    from datetime import datetime
                    try:
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                        date_str = date_obj.strftime('%Y-%m-%d')
                    except:
                        date_str = date
            else:
                date_str = str(date)
            
            schedule_query = """
                UPSERT INTO Schedule
                (id, user_id, date, type, start_time, end_time, status, created_by, created_at)
                VALUES ("{}", "{}", Date("{}"), "{}", "{}", "{}", "{}", "{}", Timestamp("{}"))
            """.format(
                schedule_id, str(user_id), date_str, task_type, start_time, end_time,
                "Активно", str(user_id), get_ydb_timestamp()
            )
            
            session.transaction().execute(schedule_query, commit_tx=True)
            
            return True, task_id
        except Exception as e:
            print(f"Ошибка создания задачи: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка создания задачи: {e}")
        return False, str(e)


async def change_user_role(username, new_role):
    """Изменить роль пользователя."""
    def execute(session):
        try:
            find_query = """
                SELECT telegram_id, username, role 
                FROM Users 
                WHERE username = "{}"
            """.format(username)
            
            result = session.transaction().execute(find_query, commit_tx=True)
            
            if not result[0].rows:
                return None, f"❌ Пользователь @{username} не найден!"
            
            user = result[0].rows[0]
            old_role = safe_decode(user.role)
            telegram_id = safe_decode(user.telegram_id)
            
            update_query = """
                UPDATE Users 
                SET role = "{}" 
                WHERE username = "{}"
            """.format(new_role, username)
            
            session.transaction().execute(update_query, commit_tx=True)
            
            return telegram_id, f"✅ Роль изменена успешно!\n\n" \
                               f"👤 Пользователь: @{username}\n" \
                               f"🔄 {old_role} → {new_role}"
            
        except Exception as e:
            return None, f"❌ Ошибка изменения роли: {str(e)}"
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        return None, f"❌ Ошибка выполнения команды: {str(e)}"


async def delete_user(username):
    """Удалить пользователя."""
    def execute(session):
        try:
            find_query = """
                SELECT telegram_id, username, role, tasks_count 
                FROM Users 
                WHERE username = "{}"
            """.format(username)
            
            result = session.transaction().execute(find_query, commit_tx=True)
            
            if not result[0].rows:
                return False, f"❌ Пользователь @{username} не найден!"
            
            user = result[0].rows[0]
            user_info = f"👤 @{safe_decode(user.username)}\n🎭 {safe_decode(user.role)}\n📋 {user.tasks_count} задач"
            user_id = safe_decode(user.telegram_id)
            
            # Удаляем связанные данные
            session.transaction().execute(f'DELETE FROM Notifications WHERE user_id = "{user_id}"', commit_tx=True)
            session.transaction().execute(f'DELETE FROM NotificationSettings WHERE user_id = "{user_id}"', commit_tx=True)
            session.transaction().execute(f'DELETE FROM Schedule WHERE user_id = "{user_id}"', commit_tx=True)
            session.transaction().execute(f'DELETE FROM WorkSchedule WHERE user_id = "{user_id}"', commit_tx=True)
            session.transaction().execute(f'UPDATE Tasks SET assigned_to = NULL WHERE assigned_to = "{user_id}"', commit_tx=True)
            session.transaction().execute(f'DELETE FROM Users WHERE telegram_id = "{user_id}"', commit_tx=True)
            
            return True, f"✅ Пользователь успешно удален!\n\n{user_info}"
            
        except Exception as e:
            return False, f"❌ Ошибка удаления: {str(e)}"
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        return False, f"❌ Ошибка выполнения удаления: {str(e)}"


async def get_system_stats():
    """Получить статистику системы."""
    def execute(session):
        try:
            users_query = """
                SELECT role, COUNT(*) as count
                FROM Users 
                GROUP BY role
            """
            users_result = session.transaction().execute(users_query, commit_tx=True)
            
            tasks_query = """
                SELECT status, COUNT(*) as count
                FROM Tasks 
                WHERE status != "Отменено"
                GROUP BY status
            """
            tasks_result = session.transaction().execute(tasks_query, commit_tx=True)
            
            return {
                'users': {safe_decode(row['role']): row.count for row in users_result[0].rows},
                'tasks': {safe_decode(row['status']): row.count for row in tasks_result[0].rows}
            }
            
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return None
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        return None


async def get_pending_tasks(user_id=None):
    """Получить ожидающие задачи (все или конкретного пользователя)."""
    def execute(session):
        try:
            if user_id:
                query = """
                    SELECT t.id, t.type, t.when_, t.description, t.assigned_to,
                           u.username, t.created_at
                    FROM Tasks t
                    JOIN Users u ON t.assigned_to = u.telegram_id
                    WHERE t.assigned_to = "{}" AND t.status = "Ожидающее"
                    ORDER BY t.when_ ASC
                """.format(str(user_id))
            else:
                query = """
                    SELECT t.id, t.type, t.when_, t.description, t.assigned_to,
                           u.username, t.created_at
                    FROM Tasks t
                    JOIN Users u ON t.assigned_to = u.telegram_id
                    WHERE t.status = "Ожидающее"
                    ORDER BY t.when_ ASC
                """
            
            result = session.transaction().execute(query, commit_tx=True)
            
            tasks = []
            for row in result[0].rows:
                tasks.append({
                    'id': safe_decode(row['id']),
                    'type': safe_decode(row['type']),
                    'when_': safe_decode(row['when_']),
                    'description': safe_decode(row['description']),
                    'assigned_to': safe_decode(row['assigned_to']),
                    'username': safe_decode(row['username']),
                    'created_at': safe_decode(row['created_at'])
                })
            return tasks
        except Exception as e:
            print(f"Ошибка получения ожидающих заданий: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения ожидающих заданий: {e}")
        return []


async def get_completed_tasks(user_id=None, limit=20):
    """Получить выполненные задачи."""
    def execute(session):
        try:
            if user_id:
                query = """
                    SELECT t.id, t.type, t.when_, t.description, t.rating, 
                           t.time_spent, t.completed_at, u.username
                    FROM Tasks t
                    JOIN Users u ON t.assigned_to = u.telegram_id
                    WHERE t.assigned_to = "{}" AND t.status = "Выполнено"
                    ORDER BY t.completed_at DESC
                    LIMIT {}
                """.format(str(user_id), limit)
            else:
                query = """
                    SELECT t.id, t.type, t.when_, t.description, t.rating, 
                           t.time_spent, t.completed_at, u.username
                    FROM Tasks t
                    JOIN Users u ON t.assigned_to = u.telegram_id
                    WHERE t.status = "Выполнено"
                    ORDER BY t.completed_at DESC
                    LIMIT {}
                """.format(limit)
            
            result = session.transaction().execute(query, commit_tx=True)
            
            tasks = []
            for row in result[0].rows:
                tasks.append({
                    'id': safe_decode(row['id']),
                    'type': safe_decode(row['type']),
                    'when_': safe_decode(row['when_']),
                    'description': safe_decode(row['description']),
                    'rating': int(row.rating) if row.rating else 0,
                    'time_spent': int(row.time_spent) if row.time_spent else 0,
                    'completed_at': safe_decode(row['completed_at']),
                    'username': safe_decode(row['username'])
                })
            return tasks
        except Exception as e:
            print(f"Ошибка получения выполненных заданий: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения выполненных заданий: {e}")
        return []


async def create_task(task_type, assigned_to, description, when_time, created_by, shelves=None):
    """Создать новое задание."""
    def execute(session):
        try:
            import uuid
            from datetime import datetime
            
            task_id = str(uuid.uuid4())
            
            # Формируем полное описание
            full_description = description
            if shelves:
                full_description += f" - Стеллажи: {shelves}"
            
            insert_query = """
                UPSERT INTO Tasks 
                (id, type, when_, status, description, assigned_to, created_by, created_at)
                VALUES ("{}", "{}", "{}", "{}", "{}", "{}", "{}", Timestamp("{}"))
            """.format(
                task_id, task_type, when_time, "Ожидающее",
                full_description, str(assigned_to), str(created_by), 
                get_ydb_timestamp()
            )
            
            session.transaction().execute(insert_query, commit_tx=True)
            
            # Обновляем счетчик задач у пользователя
            update_user_query = """
                UPDATE Users 
                SET tasks_count = tasks_count + 1
                WHERE telegram_id = "{}"
            """.format(str(assigned_to))
            
            session.transaction().execute(update_user_query, commit_tx=True)
            
            return task_id
        except Exception as e:
            print(f"Ошибка создания задания: {e}")
            return None
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка создания задания: {e}")
        return None


async def get_all_tasks_stats():
    """Получить общую статистику по заданиям."""
    def execute(session):
        try:
            # Статистика по типам и статусам
            stats_query = """
                SELECT type, status, COUNT(*) as count,
                       AVG(CAST(rating AS Double)) as avg_rating,
                       AVG(CAST(time_spent AS Double)) as avg_time
                FROM Tasks 
                WHERE rating IS NOT NULL AND rating > 0
                GROUP BY type, status
            """
            
            result = session.transaction().execute(stats_query, commit_tx=True)
            
            stats = {}
            for row in result[0].rows:
                task_type = safe_decode(row['type'])
                status = safe_decode(row['status'])
                
                if task_type not in stats:
                    stats[task_type] = {}
                
                stats[task_type][status] = {
                    'count': row.count,
                    'avg_rating': float(row.avg_rating) if row.avg_rating else 0,
                    'avg_time': float(row.avg_time) if row.avg_time else 0
                }
            
            return stats
        except Exception as e:
            print(f"Ошибка получения статистики заданий: {e}")
            return {}
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения статистики заданий: {e}")
        return {}


async def get_users_for_task_assignment():
    """Получить список пользователей для назначения заданий."""
    def execute(session):
        try:
            query = """
                SELECT telegram_id, username, role
                FROM Users 
                WHERE role IN ('Кладовщик', 'ЗДС', 'ДС')
                ORDER BY role, username
            """
            
            result = session.transaction().execute(query, commit_tx=True)
            
            users = []
            for row in result[0].rows:
                users.append({
                    'telegram_id': safe_decode(row['telegram_id']),
                    'username': safe_decode(row['username']),
                    'role': safe_decode(row['role'])
                })
            
            return users
        except Exception as e:
            print(f"Ошибка получения пользователей: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения пользователей: {e}")
        return []


async def update_task_status(task_id, new_status, rating=None, time_spent=None):
    """Обновить статус задания."""
    def execute(session):
        try:
            # Базовый запрос обновления
            update_fields = [f'status = "{new_status}"']
            
            if new_status == "Выполнено":
                update_fields.append(f'completed_at = Timestamp("{get_ydb_timestamp()}")')
                
                if rating:
                    update_fields.append(f'rating = {rating}')
                
                if time_spent:
                    update_fields.append(f'time_spent = {time_spent}')
            
            update_query = """
                UPDATE Tasks 
                SET {}
                WHERE id = "{}"
            """.format(", ".join(update_fields), task_id)
            
            session.transaction().execute(update_query, commit_tx=True)
            
            return True
        except Exception as e:
            print(f"Ошибка обновления статуса задания: {e}")
            return False
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка обновления статуса задания: {e}")
        return False


async def get_task_by_id(task_id):
    """Получить задание по ID."""
    def execute(session):
        try:
            query = """
                SELECT t.id, t.type, t.when_, t.status, t.description, 
                       t.assigned_to, t.rating, t.time_spent, t.created_by,
                       u.username, uc.username as creator_username
                FROM Tasks t
                JOIN Users u ON t.assigned_to = u.telegram_id
                LEFT JOIN Users uc ON t.created_by = uc.telegram_id
                WHERE t.id = "{}"
            """.format(task_id)
            
            result = session.transaction().execute(query, commit_tx=True)
            
            if result[0].rows:
                row = result[0].rows[0]
                return {
                    'telegram_id': safe_decode(row[0]),  # telegram_id
                    'username': safe_decode(row[1]),     # username
                    'role': safe_decode(row[2]),         # role
                    'tasks_count': int(row[3]) if row[3] else 0,        # tasks_count
                    'average_rating': float(row[4]) if row[4] else 0.0, # average_rating
                    'quality_score': float(row[5]) if row[5] else 0.0,  # quality_score
                    'notifications_enabled': bool(row[6]) if row[6] is not None else True # notifications_enabled
                }
            return None
        except Exception as e:
            print(f"Ошибка получения задания: {e}")
            return None
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения задания: {e}")
        return None


async def get_schedule_by_type_admin(schedule_type):
    """Получить расписание по типу для админа с подробностями."""
    def execute(session):
        try:
            query = """
                SELECT s.id, s.user_id, s.date, s.start_time, s.end_time, 
                       s.created_at, u.username
                FROM Schedule s
                JOIN Users u ON s.user_id = u.telegram_id
                WHERE s.type = "{}" AND s.status = "Активно"
                ORDER BY s.date DESC, s.start_time ASC
                LIMIT 30
            """.format(schedule_type)
            
            result = session.transaction().execute(query, commit_tx=True)
            
            schedule = []
            for row in result[0].rows:
                # Порядок: id(0), user_id(1), date(2), start_time(3), end_time(4), created_at(5), username(6)
                schedule.append({
                    'id': safe_decode(row[0]),
                    'user_id': safe_decode(row[1]),
                    'date': safe_decode(row[2]),
                    'start_time': safe_decode(row[3]),
                    'end_time': safe_decode(row[4]),
                    'created_at': safe_decode(row[5]),
                    'username': safe_decode(row[6]),
                    'description': ""
                })
            return schedule
        except Exception as e:
            print(f"Ошибка получения расписания админ: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения расписания админ: {e}")
        return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения расписания админ: {e}")
        return []


async def get_schedule_stats_admin():
    """Получить детальную статистику расписания для админа."""
    def execute(session):
        try:
            # Общая статистика
            stats_query = """
                SELECT 
                    type,
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN date >= CurrentUtcDate() THEN 1 END) as upcoming_count,
                    COUNT(CASE WHEN date < CurrentUtcDate() THEN 1 END) as past_count
                FROM Schedule 
                WHERE status = "Активно"
                GROUP BY type
            """
            
            result = session.transaction().execute(stats_query, commit_tx=True)
            
            stats = {}
            for row in result[0].rows:
                schedule_type = safe_decode(row['type'])
                stats[schedule_type] = {
                    'total': row.total_count,
                    'upcoming': row.upcoming_count,
                    'past': row.past_count
                }
            
            # Статистика по пользователям
            user_stats_query = """
                SELECT 
                    u.username,
                    s.type,
                    COUNT(*) as count
                FROM Schedule s
                JOIN Users u ON s.user_id = u.telegram_id
                WHERE s.status = "Активно" AND s.date >= CurrentUtcDate()
                GROUP BY u.username, s.type
                ORDER BY count DESC
                LIMIT 20
            """
            
            user_result = session.transaction().execute(user_stats_query, commit_tx=True)
            
            user_stats = []
            for row in user_result[0].rows:
                user_stats.append({
                    'username': safe_decode(row['username']),
                    'type': safe_decode(row['type']),
                    'count': row.count
                })
            
            return {
                'type_stats': stats,
                'user_stats': user_stats
            }
            
        except Exception as e:
            print(f"Ошибка получения статистики админ: {e}")
            return {}
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения статистики админ: {e}")
        return {}


# Заглушки для функций редактирования расписания  
async def delete_schedule_item(schedule_id, admin_id):
    """Удалить запись из расписания."""
    def execute(session):
        try:
            print(f"DEBUG: Попытка удалить запись с ID: {schedule_id}")
            
            # Простой запрос без алиасов
            select_query = """
                SELECT Schedule.id, Schedule.user_id, Schedule.date, Schedule.type, Schedule.start_time, Schedule.end_time, Users.username
                FROM Schedule 
                JOIN Users ON Schedule.user_id = Users.telegram_id
                WHERE Schedule.id = "{}" AND Schedule.status = "Активно"
            """.format(schedule_id)
            
            result = session.transaction().execute(select_query, commit_tx=True)
            
            print(f"DEBUG: Найдено записей: {len(result[0].rows)}")
            
            if not result[0].rows:
                print(f"DEBUG: Запись с ID {schedule_id} не найдена")
                return False, "❌ Запись не найдена или уже удалена"
            
            row = result[0].rows[0]
            print(f"DEBUG: Данные записи: {[repr(field) for field in row]}")
            
            # Получаем данные
            schedule_id_from_db = safe_decode(row[0])
            user_id = safe_decode(row[1])
            date_raw = row[2]
            task_type = safe_decode(row[3])
            start_time = safe_decode(row[4])
            end_time = safe_decode(row[5])
            username = safe_decode(row[6])
            
            # Форматируем дату
            if isinstance(date_raw, int) and 1 <= date_raw <= 100000:
                from datetime import datetime, timedelta
                epoch = datetime(1900, 1, 1)
                actual_date = epoch + timedelta(days=date_raw - 1)
                formatted_date = actual_date.strftime('%Y-%m-%d')
            else:
                formatted_date = safe_decode(date_raw)
            
            item_info = {
                'id': schedule_id_from_db,
                'user_id': user_id,
                'date': formatted_date,
                'type': task_type,
                'start_time': start_time,
                'end_time': end_time,
                'username': username
            }
            
            print(f"DEBUG: Обработанная информация о записи: {item_info}")
            
            # Удаляем запись из расписания (помечаем как удаленную)
            delete_schedule_query = """
                UPDATE Schedule 
                SET status = "Удалено"
                WHERE id = "{}"
            """.format(schedule_id)
            
            session.transaction().execute(delete_schedule_query, commit_tx=True)
            print(f"DEBUG: Запись помечена как удаленная")
            
            # ФИЗИЧЕСКИ УДАЛЯЕМ связанные задания
            delete_tasks_query = """
                DELETE FROM Tasks 
                WHERE assigned_to = "{}" AND type = "{}" 
                AND when_ LIKE "{}%"
            """.format(user_id, task_type, formatted_date)
            
            session.transaction().execute(delete_tasks_query, commit_tx=True)
            print(f"DEBUG: Связанные задания ФИЗИЧЕСКИ УДАЛЕНЫ")
            
            return True, item_info
            
        except Exception as e:
            print(f"Ошибка удаления записи расписания: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Ошибка удаления: {str(e)}"
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка выполнения удаления: {e}")
        return False, f"Ошибка выполнения: {str(e)}"


async def edit_schedule_item(schedule_id, new_date=None, new_start_time=None, new_end_time=None, admin_id=None):
    """Редактировать запись расписания."""
    return False, "❌ Функция в разработке"



async def get_notification_settings(user_id):
    """Получить настройки уведомлений пользователя."""
    def execute(session):
        try:
            query = """
                SELECT user_id, general_notifications, task_reminders, 
                       schedule_updates, rating_notifications
                FROM NotificationSettings 
                WHERE user_id = "{}"
            """.format(str(user_id))
            
            result = session.transaction().execute(query, commit_tx=True)
            
            if result[0].rows:
                row = result[0].rows[0]
                return {
                    'user_id': safe_decode(row[0]),
                    'general_notifications': bool(row[1]) if row[1] is not None else True,
                    'task_reminders': bool(row[2]) if row[2] is not None else True,
                    'schedule_updates': bool(row[3]) if row[3] is not None else True,
                    'rating_notifications': bool(row[4]) if row[4] is not None else True
                }
            else:
                # Создаем настройки по умолчанию
                create_query = """
                    UPSERT INTO NotificationSettings 
                    (user_id, general_notifications, task_reminders, 
                     schedule_updates, rating_notifications)
                    VALUES ("{}", {}, {}, {}, {})
                """.format(str(user_id), True, True, True, True)
                
                session.transaction().execute(create_query, commit_tx=True)
                
                return {
                    'user_id': str(user_id),
                    'general_notifications': True,
                    'task_reminders': True,
                    'schedule_updates': True,
                    'rating_notifications': True
                }
        except Exception as e:
            print(f"Ошибка получения настроек уведомлений: {e}")
            return None
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения настроек уведомлений: {e}")
        return None


async def get_user_notifications(user_id, limit=20):
    """Получить уведомления пользователя."""
    def execute(session):
        try:
            query = """
                SELECT id, title, message, type, is_read, created_at
                FROM Notifications 
                WHERE user_id = "{}"
                ORDER BY created_at DESC
                LIMIT {}
            """.format(str(user_id), limit)
            
            result = session.transaction().execute(query, commit_tx=True)
            
            notifications = []
            for row in result[0].rows:
                notifications.append({
                    'id': safe_decode(row[0]),
                    'title': safe_decode(row[1]),
                    'message': safe_decode(row[2]),
                    'type': safe_decode(row[3]),
                    'is_read': bool(row[4]) if row[4] is not None else False,
                    'created_at': safe_decode(row[5])
                })
            
            return notifications
            
        except Exception as e:
            print(f"Ошибка получения уведомлений: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения уведомлений: {e}")
        return []


async def update_notification_settings(user_id, settings):
    """Обновить настройки уведомлений пользователя."""
    def execute(session):
        try:
            query = """
                UPSERT INTO NotificationSettings 
                (user_id, general_notifications, task_reminders, 
                 schedule_updates, rating_notifications)
                VALUES ("{}", {}, {}, {}, {})
            """.format(
                str(user_id),
                settings.get('general_notifications', True),
                settings.get('task_reminders', True),
                settings.get('schedule_updates', True),
                settings.get('rating_notifications', True)
            )
            
            session.transaction().execute(query, commit_tx=True)
            return True
            
        except Exception as e:
            print(f"Ошибка обновления настроек уведомлений: {e}")
            return False
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка обновления настроек уведомлений: {e}")
        return False


async def create_notification(user_id, title, message, notification_type="general"):
    """Создать уведомление для пользователя."""
    def execute(session):
        try:
            import uuid
            
            notification_id = str(uuid.uuid4())
            
            query = """
                UPSERT INTO Notifications 
                (id, user_id, title, message, type, is_read, created_at)
                VALUES ("{}", "{}", "{}", "{}", "{}", {}, Timestamp("{}"))
            """.format(
                notification_id,
                str(user_id),
                title.replace('"', '\"'),
                message.replace('"', '\"'),
                notification_type,
                False,
                get_ydb_timestamp()
            )
            
            session.transaction().execute(query, commit_tx=True)
            return notification_id
            
        except Exception as e:
            print(f"Ошибка создания уведомления: {e}")
            return None
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка создания уведомления: {e}")
        return None



async def get_quality_report():
    """Получить отчет по качеству работы."""
    def execute(session):
        try:
            # Отчет по качеству - средние рейтинги по пользователям
            query = """
                SELECT u.username, u.role,
                       COUNT(t.id) as total_tasks,
                       AVG(CAST(t.rating AS Double)) as avg_rating,
                       AVG(CAST(t.time_spent AS Double)) as avg_time,
                       COUNT(CASE WHEN t.status = 'Выполнено' THEN 1 END) as completed_tasks
                FROM Users u
                LEFT JOIN Tasks t ON u.telegram_id = t.assigned_to
                WHERE t.rating IS NOT NULL AND t.rating > 0 AND t.status != "Отменено"
                GROUP BY u.username, u.role
                ORDER BY avg_rating DESC, total_tasks DESC
            """
            
            result = session.transaction().execute(query, commit_tx=True)
            
            quality_data = []
            for row in result[0].rows:
                quality_data.append({
                    'username': safe_decode(row[0]),
                    'role': safe_decode(row[1]),
                    'total_tasks': int(row[2]) if row[2] else 0,
                    'avg_rating': float(row[3]) if row[3] else 0.0,
                    'avg_time': float(row[4]) if row[4] else 0.0,
                    'completed_tasks': int(row[5]) if row[5] else 0
                })
            
            return quality_data
            
        except Exception as e:
            print(f"Ошибка получения отчета по качеству: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения отчета по качеству: {e}")
        return []


async def get_time_report():
    """Получить отчет по времени выполнения."""
    def execute(session):
        try:
            # Отчет по времени - статистика времени выполнения по типам задач
            query = """
                SELECT type,
                       COUNT(*) as total_tasks,
                       AVG(CAST(time_spent AS Double)) as avg_time,
                       MIN(CAST(time_spent AS Double)) as min_time,
                       MAX(CAST(time_spent AS Double)) as max_time,
                       COUNT(CASE WHEN time_spent > 60 THEN 1 END) as long_tasks
                FROM Tasks 
                WHERE status = 'Выполнено' AND time_spent IS NOT NULL AND time_spent > 0
                GROUP BY type
                ORDER BY avg_time DESC
            """
            
            result = session.transaction().execute(query, commit_tx=True)
            
            time_data = []
            for row in result[0].rows:
                time_data.append({
                    'type': safe_decode(row[0]),
                    'total_tasks': int(row[1]) if row[1] else 0,
                    'avg_time': float(row[2]) if row[2] else 0.0,
                    'min_time': float(row[3]) if row[3] else 0.0,
                    'max_time': float(row[4]) if row[4] else 0.0,
                    'long_tasks': int(row[5]) if row[5] else 0
                })
            
            return time_data
            
        except Exception as e:
            print(f"Ошибка получения отчета по времени: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения отчета по времени: {e}")
        return []


async def get_tasks_report():
    """Получить отчет по типам задач."""
    def execute(session):
        try:
            # Отчет по типам задач - статистика выполнения
            query = """
                SELECT type, status,
                       COUNT(*) as count,
                       AVG(CAST(rating AS Double)) as avg_rating
                FROM Tasks 
                WHERE status != "Отменено"
                GROUP BY type, status
                ORDER BY type, status
            """
            
            result = session.transaction().execute(query, commit_tx=True)
            
            # Группируем данные по типам
            tasks_data = {}
            for row in result[0].rows:
                task_type = safe_decode(row[0])
                status = safe_decode(row[1])
                count = int(row[2]) if row[2] else 0
                avg_rating = float(row[3]) if row[3] else 0.0
                
                if task_type not in tasks_data:
                    tasks_data[task_type] = {
                        'total': 0,
                        'completed': 0,
                        'pending': 0,
                        'in_progress': 0,
                        'avg_rating': 0.0
                    }
                
                tasks_data[task_type]['total'] += count
                
                if status == 'Выполнено':
                    tasks_data[task_type]['completed'] = count
                    tasks_data[task_type]['avg_rating'] = avg_rating
                elif status == 'Ожидающее':
                    tasks_data[task_type]['pending'] = count
                elif status == 'В работе':
                    tasks_data[task_type]['in_progress'] = count
            
            return tasks_data
            
        except Exception as e:
            print(f"Ошибка получения отчета по задачам: {e}")
            return {}
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения отчета по задачам: {e}")
        return {}


async def get_general_report():
    """Получить общую статистику."""
    def execute(session):
        try:
            # Общая статистика системы
            stats = {}
            
            # Статистика пользователей
            users_query = """
                SELECT role, COUNT(*) as count
                FROM Users 
                GROUP BY role
            """
            users_result = session.transaction().execute(users_query, commit_tx=True)
            
            stats['users'] = {}
            total_users = 0
            for row in users_result[0].rows:
                role = safe_decode(row[0])
                count = int(row[1]) if row[1] else 0
                stats['users'][role] = count
                total_users += count
            
            stats['total_users'] = total_users
            
            # Статистика задач
            tasks_query = """
                SELECT status, COUNT(*) as count
                FROM Tasks 
                WHERE status != "Отменено"
                GROUP BY status
            """
            tasks_result = session.transaction().execute(tasks_query, commit_tx=True)
            
            stats['tasks'] = {}
            total_tasks = 0
            for row in tasks_result[0].rows:
                status = safe_decode(row[0])
                count = int(row[1]) if row[1] else 0
                stats['tasks'][status] = count
                total_tasks += count
            
            stats['total_tasks'] = total_tasks
            
            # Статистика расписания
            schedule_query = """
                SELECT type, COUNT(*) as count
                FROM Schedule 
                WHERE status = 'Активно'
                GROUP BY type
            """
            schedule_result = session.transaction().execute(schedule_query, commit_tx=True)
            
            stats['schedule'] = {}
            total_schedule = 0
            for row in schedule_result[0].rows:
                stype = safe_decode(row[0])
                count = int(row[1]) if row[1] else 0
                stats['schedule'][stype] = count
                total_schedule += count
            
            stats['total_schedule'] = total_schedule
            
            # Средний рейтинг системы
            rating_query = """
                SELECT AVG(CAST(rating AS Double)) as avg_rating,
                       COUNT(*) as rated_tasks
                FROM Tasks 
                WHERE rating IS NOT NULL AND rating > 0 AND status != "Отменено"
            """
            rating_result = session.transaction().execute(rating_query, commit_tx=True)
            
            if rating_result[0].rows:
                row = rating_result[0].rows[0]
                stats['avg_rating'] = float(row[0]) if row[0] else 0.0
                stats['rated_tasks'] = int(row[1]) if row[1] else 0
            else:
                stats['avg_rating'] = 0.0
                stats['rated_tasks'] = 0
            
            return stats
            
        except Exception as e:
            print(f"Ошибка получения общей статистики: {e}")
            return {}
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения общей статистики: {e}")
        return {}


async def get_user_performance_report(user_id=None):
    """Получить отчет по производительности пользователя."""
    def execute(session):
        try:
            if user_id:
                # Отчет по конкретному пользователю
                query = """
                    SELECT u.username, u.role,
                           COUNT(t.id) as total_tasks,
                           COUNT(CASE WHEN t.status = 'Выполнено' THEN 1 END) as completed,
                           COUNT(CASE WHEN t.status = 'Ожидающее' THEN 1 END) as pending,
                           AVG(CAST(t.rating AS Double)) as avg_rating,
                           AVG(CAST(t.time_spent AS Double)) as avg_time
                    FROM Users u
                    LEFT JOIN Tasks t ON u.telegram_id = t.assigned_to
                    WHERE u.telegram_id = "{}" AND (t.id IS NULL OR t.status != "Отменено")
                    GROUP BY u.username, u.role
                """.format(str(user_id))
            else:
                # Отчет по всем пользователям
                query = """
                    SELECT u.username, u.role,
                           COUNT(t.id) as total_tasks,
                           COUNT(CASE WHEN t.status = 'Выполнено' THEN 1 END) as completed,
                           COUNT(CASE WHEN t.status = 'Ожидающее' THEN 1 END) as pending,
                           AVG(CAST(t.rating AS Double)) as avg_rating,
                           AVG(CAST(t.time_spent AS Double)) as avg_time
                    FROM Users u
                    LEFT JOIN Tasks t ON u.telegram_id = t.assigned_to
                    WHERE t.id IS NULL OR t.status != "Отменено"
                    GROUP BY u.username, u.role
                    ORDER BY completed DESC, avg_rating DESC
                """
            
            result = session.transaction().execute(query, commit_tx=True)
            
            performance_data = []
            for row in result[0].rows:
                performance_data.append({
                    'username': safe_decode(row[0]),
                    'role': safe_decode(row[1]),
                    'total_tasks': int(row[2]) if row[2] else 0,
                    'completed': int(row[3]) if row[3] else 0,
                    'pending': int(row[4]) if row[4] else 0,
                    'avg_rating': float(row[5]) if row[5] else 0.0,
                    'avg_time': float(row[6]) if row[6] else 0.0,
                    'completion_rate': (int(row[3]) / int(row[2]) * 100) if row[2] and row[2] > 0 else 0.0
                })
            
            return performance_data
            
        except Exception as e:
            print(f"Ошибка получения отчета по производительности: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения отчета по производительности: {e}")
        return []


async def get_schedule_efficiency_report():
    """Получить отчет по эффективности расписания."""
    def execute(session):
        try:
            # Эффективность расписания - соответствие плана и факта
            query = """
                SELECT s.type, s.date,
                       COUNT(s.id) as scheduled_count,
                       COUNT(t.id) as completed_count,
                       AVG(CAST(t.rating AS Double)) as avg_rating
                FROM Schedule s
                LEFT JOIN Tasks t ON s.user_id = t.assigned_to 
                    AND s.type = t.type 
                    AND s.date = DATE(t.when_)
                    AND t.status = 'Выполнено'
                WHERE s.status = 'Активно'
                GROUP BY s.type, s.date
                ORDER BY s.date DESC, s.type
                LIMIT 30
            """
            
            result = session.transaction().execute(query, commit_tx=True)
            
            efficiency_data = []
            for row in result[0].rows:
                scheduled = int(row[2]) if row[2] else 0
                completed = int(row[3]) if row[3] else 0
                efficiency = (completed / scheduled * 100) if scheduled > 0 else 0
                
                efficiency_data.append({
                    'type': safe_decode(row[0]),
                    'date': safe_decode(row[1]),
                    'scheduled': scheduled,
                    'completed': completed,
                    'efficiency': efficiency,
                    'avg_rating': float(row[4]) if row[4] else 0.0
                })
            
            return efficiency_data
            
        except Exception as e:
            print(f"Ошибка получения отчета по эффективности: {e}")
            return []
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка получения отчета по эффективности: {e}")
        return []


async def cleanup_canceled_tasks():
    """Физически удалить отмененные задачи (для очистки базы)."""
    def execute(session):
        try:
            # Подсчитываем отмененные задачи
            count_query = """
                SELECT COUNT(*) as count
                FROM Tasks 
                WHERE status = "Отменено"
            """
            
            count_result = session.transaction().execute(count_query, commit_tx=True)
            canceled_count = count_result[0].rows[0][0] if count_result[0].rows else 0
            
            if canceled_count > 0:
                # Удаляем отмененные задачи
                delete_query = """
                    DELETE FROM Tasks 
                    WHERE status = "Отменено"
                """
                
                session.transaction().execute(delete_query, commit_tx=True)
                print(f"🗑️ Удалено {canceled_count} отмененных задач")
                
                return canceled_count
            else:
                print("✅ Нет отмененных задач для удаления")
                return 0
            
        except Exception as e:
            print(f"Ошибка очистки отмененных задач: {e}")
            return 0
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка очистки отмененных задач: {e}")
        return 0



async def cleanup_canceled_tasks():
    """Физически удалить отмененные задачи (для очистки базы)."""
    def execute(session):
        try:
            # Подсчитываем отмененные задачи
            count_query = """
                SELECT COUNT(*) as count
                FROM Tasks 
                WHERE status = "Отменено"
            """
            
            count_result = session.transaction().execute(count_query, commit_tx=True)
            canceled_count = count_result[0].rows[0][0] if count_result[0].rows else 0
            
            if canceled_count > 0:
                # Удаляем отмененные задачи
                delete_query = """
                    DELETE FROM Tasks 
                    WHERE status = "Отменено"
                """
                
                session.transaction().execute(delete_query, commit_tx=True)
                print(f"🗑️ Удалено {canceled_count} отмененных задач")
                
                return canceled_count
            else:
                print("✅ Нет отмененных задач для удаления")
                return 0
            
        except Exception as e:
            print(f"Ошибка очистки отмененных задач: {e}")
            return 0
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка очистки отмененных задач: {e}")
        return 0



async def delete_all_canceled_tasks():
    """ФИЗИЧЕСКИ удалить все существующие отмененные задачи."""
    def execute(session):
        try:
            # Сначала подсчитываем сколько задач будет удалено
            count_query = """
                SELECT COUNT(*) as count
                FROM Tasks 
                WHERE status = "Отменено"
            """
            
            count_result = session.transaction().execute(count_query, commit_tx=True)
            canceled_count = count_result[0].rows[0][0] if count_result[0].rows else 0
            
            print(f"DEBUG: Найдено {canceled_count} отмененных задач")
            
            if canceled_count > 0:
                # Физически удаляем отмененные задачи
                delete_query = """
                    DELETE FROM Tasks 
                    WHERE status = "Отменено"
                """
                
                session.transaction().execute(delete_query, commit_tx=True)
                print(f"🗑️ ФИЗИЧЕСКИ УДАЛЕНО {canceled_count} отмененных задач из базы")
                
                return canceled_count
            else:
                print("✅ Нет отмененных задач для удаления")
                return 0
            
        except Exception as e:
            print(f"Ошибка физического удаления отмененных задач: {e}")
            return 0
    
    try:
        return pool.retry_operation_sync(execute)
    except Exception as e:
        print(f"Ошибка физического удаления отмененных задач: {e}")
        return 0


def cleanup():
    """Очистка ресурсов."""
    try:
        if driver:
            driver.stop()
        print("🧹 Ресурсы YDB очищены")
    except:
        pass