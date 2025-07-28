#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API для работы с базой данных через threading
"""

import logging
from .utils import run_async_in_thread

logger = logging.getLogger(__name__)

class DatabaseAPI:
    """Класс для работы с базой данных через threading"""
    
    @staticmethod
    def is_admin(user_id):
        """Проверить админа"""
        from config import ADMINS
        return user_id in ADMINS
    
    @staticmethod
    def get_or_create_user(user_id, username=None):
        """Получить или создать пользователя"""
        try:
            from database import get_or_create_user
            return run_async_in_thread(get_or_create_user(user_id, username))
        except Exception as e:
            logger.error(f"❌ Ошибка get_or_create_user: {e}")
            return None
    
    @staticmethod
    def get_all_users():
        """Получить всех пользователей"""
        try:
            from database import get_all_users
            return run_async_in_thread(get_all_users())
        except Exception as e:
            logger.error(f"❌ Ошибка get_all_users: {e}")
            return []
    
    @staticmethod
    def get_my_tasks(user_id):
        """Получить задачи пользователя"""
        try:
            from database import get_my_tasks
            return run_async_in_thread(get_my_tasks(user_id))
        except Exception as e:
            logger.error(f"❌ Ошибка get_my_tasks: {e}")
            return []
    
    @staticmethod
    def get_pending_tasks(user_id=None):
        """Получить ожидающие задачи"""
        try:
            from database import get_pending_tasks
            return run_async_in_thread(get_pending_tasks(user_id))
        except Exception as e:
            logger.error(f"❌ Ошибка get_pending_tasks: {e}")
            return []
    
    @staticmethod
    def get_completed_tasks(user_id=None):
        """Получить выполненные задачи"""
        try:
            from database import get_completed_tasks
            return run_async_in_thread(get_completed_tasks(user_id))
        except Exception as e:
            logger.error(f"❌ Ошибка get_completed_tasks: {e}")
            return []
    
    @staticmethod
    def get_schedule_by_type(schedule_type):
        """Получить расписание по типу"""
        try:
            from database import get_schedule_by_type
            return run_async_in_thread(get_schedule_by_type(schedule_type))
        except Exception as e:
            logger.error(f"❌ Ошибка get_schedule_by_type: {e}")
            return []
    
    @staticmethod
    def create_schedule_task(user_id, task_type, date, time_slot, shelves=None):
        """Создать задачу в расписании"""
        try:
            from database import create_schedule_task
            return run_async_in_thread(create_schedule_task(user_id, task_type, date, time_slot, shelves))
        except Exception as e:
            logger.error(f"❌ Ошибка create_schedule_task: {e}")
            return False, str(e)
    
    @staticmethod
    def delete_schedule_item(schedule_id, admin_id):
        """Удалить запись из расписания"""
        try:
            from database import delete_schedule_item
            return run_async_in_thread(delete_schedule_item(schedule_id, admin_id))
        except Exception as e:
            logger.error(f"❌ Ошибка delete_schedule_item: {e}")
            return False, str(e)
    
    # Методы уведомлений
    @staticmethod
    def get_notification_settings(user_id):
        """Получить настройки уведомлений пользователя"""
        try:
            from database import get_notification_settings
            return run_async_in_thread(get_notification_settings(user_id))
        except Exception as e:
            logger.error(f"❌ Ошибка get_notification_settings: {e}")
            return None
    
    @staticmethod
    def get_user_notifications(user_id, limit=20):
        """Получить уведомления пользователя"""
        try:
            from database import get_user_notifications
            return run_async_in_thread(get_user_notifications(user_id, limit))
        except Exception as e:
            logger.error(f"❌ Ошибка get_user_notifications: {e}")
            return []
    
    @staticmethod
    def update_notification_settings(user_id, settings):
        """Обновить настройки уведомлений"""
        try:
            from database import update_notification_settings
            return run_async_in_thread(update_notification_settings(user_id, settings))
        except Exception as e:
            logger.error(f"❌ Ошибка update_notification_settings: {e}")
            return False
    
    @staticmethod
    def create_notification(user_id, title, message, notification_type="general"):
        """Создать уведомление"""
        try:
            from database import create_notification
            return run_async_in_thread(create_notification(user_id, title, message, notification_type))
        except Exception as e:
            logger.error(f"❌ Ошибка create_notification: {e}")
            return False
    
    @staticmethod
    def send_notification_to_all_users(title, message, role_filter=None):
        """Отправить уведомление всем пользователям"""
        try:
            from .utils import TelegramAPI
            from config import TOKEN
            
            api = TelegramAPI(TOKEN)
            users = DatabaseAPI.get_all_users()
            sent_count = 0
            
            for user in users:
                # Фильтр по роли если указан
                if role_filter and user.get('role') != role_filter:
                    continue
                
                # Проверяем настройки пользователя
                settings = DatabaseAPI.get_notification_settings(user['telegram_id'])
                if not settings or not settings.get('general_notifications', True):
                    continue
                
                # Создаем уведомление в базе
                DatabaseAPI.create_notification(user['telegram_id'], title, message)
                
                # Отправляем через Telegram
                notification_text = f"🔔 *{title}*\n\n{message}"
                success, result = api.send_message(user['telegram_id'], notification_text)
                if success:
                    sent_count += 1
            
            return sent_count
        except Exception as e:
            logger.error(f"❌ Ошибка send_notification_to_all_users: {e}")
            return 0
    
    # Методы отчетов
    @staticmethod
    def get_quality_report():
        """Получить отчет по качеству работы"""
        try:
            from database import get_quality_report
            return run_async_in_thread(get_quality_report())
        except Exception as e:
            logger.error(f"❌ Ошибка get_quality_report: {e}")
            return None
    
    @staticmethod
    def get_time_report():
        """Получить отчет по времени выполнения"""
        try:
            from database import get_time_report
            return run_async_in_thread(get_time_report())
        except Exception as e:
            logger.error(f"❌ Ошибка get_time_report: {e}")
            return None
    
    @staticmethod
    def get_tasks_report():
        """Получить отчет по типам задач"""
        try:
            from database import get_tasks_report
            return run_async_in_thread(get_tasks_report())
        except Exception as e:
            logger.error(f"❌ Ошибка get_tasks_report: {e}")
            return None
    
    @staticmethod
    def get_general_report():
        """Получить общую статистику"""
        try:
            from database import get_general_report
            return run_async_in_thread(get_general_report())
        except Exception as e:
            logger.error(f"❌ Ошибка get_general_report: {e}")
            return None
