#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/utils.py
Утилиты для работы с Telegram API
"""

import requests
import json
import logging

logger = logging.getLogger(__name__)

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
            
            response = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
            
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
            
            response = requests.post(f"{self.api_url}/editMessageText", json=payload, timeout=10)
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
            
            response = requests.post(f"{self.api_url}/answerCallbackQuery", json=payload, timeout=5)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ Ошибка answer callback: {e}")
            return False


def is_admin(user_id):
    """Проверить является ли пользователь админом"""
    import os
    admin_users_str = os.environ.get('ADMIN_USERS', '398232017,1014841100')
    admins = [int(uid.strip()) for uid in admin_users_str.split(',') if uid.strip()]
    return user_id in admins


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