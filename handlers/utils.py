#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Утилиты для работы хендлеров
"""

import threading
import requests
import json
from datetime import datetime
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# HTTP сессия
session = requests.Session()
session.timeout = 30

def run_async_in_thread(coro):
    """Запускает async функцию в отдельном потоке"""
    result = [None]
    error = [None]
    
    def worker():
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result[0] = loop.run_until_complete(coro)
            finally:
                loop.close()
        except Exception as e:
            error[0] = e
    
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=10)
    
    if error[0]:
        raise error[0]
    return result[0]


class TelegramAPI:
    """Класс для работы с Telegram API"""
    
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, chat_id, text, reply_markup=None, parse_mode='Markdown'):
        """Отправляет сообщение"""
        try:
            payload = {
                'chat_id': chat_id,
                'text': text[:4096],
                'parse_mode': parse_mode
            }
            
            if reply_markup:
                payload['reply_markup'] = json.dumps(reply_markup)
            
            response = session.post(f"{self.api_url}/sendMessage", json=payload)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                logger.error(f"❌ Ошибка отправки: {response.status_code}")
                return False, response.text
                
        except Exception as e:
            logger.error(f"❌ Исключение при отправке: {e}")
            return False, str(e)
    
    def edit_message(self, chat_id, message_id, text, reply_markup=None, parse_mode='Markdown'):
        """Редактирует сообщение"""
        try:
            payload = {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': text[:4096],
                'parse_mode': parse_mode
            }
            
            if reply_markup:
                payload['reply_markup'] = json.dumps(reply_markup)
            
            response = session.post(f"{self.api_url}/editMessageText", json=payload)
            return response.status_code == 200, response.json() if response.status_code == 200 else response.text
            
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования: {e}")
            return False, str(e)
    
    def answer_callback_query(self, callback_query_id, text=None):
        """Отвечает на callback query"""
        try:
            payload = {'callback_query_id': callback_query_id}
            if text:
                payload['text'] = text
            
            response = session.post(f"{self.api_url}/answerCallbackQuery", json=payload)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ Ошибка answer callback: {e}")
            return False


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


def get_role_emoji(role):
    """Возвращает эмодзи для роли"""
    return {
        "ДС": "👑",
        "ЗДС": "🎖️", 
        "Кладовщик": "👷"
    }.get(role, "👤")


def get_task_type_emoji(task_type):
    """Возвращает эмодзи для типа задачи"""
    return {
        "Обеды": "🍽️",
        "Уборка": "🧹", 
        "Пересчеты": "🔢"
    }.get(task_type, "📋")


def format_date(date_string):
    """Форматирует дату для отображения"""
    try:
        if isinstance(date_string, str) and len(date_string) >= 10:
            return date_string[:10]
        return str(date_string)
    except:
        return "Неизвестно"


def safe_decode(value):
    """Безопасное декодирование значений из YDB"""
    if isinstance(value, bytes):
        return value.decode('utf-8')
    elif value is None:
        return "Unknown"
    else:
        return str(value)
