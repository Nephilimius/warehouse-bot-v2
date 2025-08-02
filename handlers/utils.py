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
        """
        Инициализация API клиента
        
        Args:
            token (str): Токен Telegram бота
        """
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, chat_id, text, reply_markup=None, parse_mode='Markdown'):
        """
        Отправляет сообщение пользователю
        
        Args:
            chat_id (int): ID чата
            text (str): Текст сообщения
            reply_markup (dict, optional): Клавиатура
            parse_mode (str): Режим парсинга (Markdown/HTML)
            
        Returns:
            tuple: (success: bool, result: dict/str)
        """
        try:
            payload = {
                'chat_id': chat_id,
                'text': text[:4096],
                'parse_mode': parse_mode
            }
            
            if reply_markup:
                payload['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(
                f"{self.api_url}/sendMessage", 
                json=payload, 
                timeout=10
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                logger.error(f"❌ Ошибка отправки: {response.status_code}")
                return False, response.text
                
        except Exception as e:
            logger.error(f"❌ Исключение при отправке: {e}")
            return False, str(e)
    
    def edit_message(self, chat_id, message_id, text, reply_markup=None, parse_mode='Markdown'):
        """
        Редактирует существующее сообщение
        
        Args:
            chat_id (int): ID чата
            message_id (int): ID сообщения для редактирования
            text (str): Новый текст сообщения
            reply_markup (dict, optional): Клавиатура
            parse_mode (str): Режим парсинга
            
        Returns:
            tuple: (success: bool, result: dict/str)
        """
        try:
            payload = {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': text[:4096],
                'parse_mode': parse_mode
            }
            
            if reply_markup:
                payload['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(
                f"{self.api_url}/editMessageText", 
                json=payload, 
                timeout=10
            )
            
            if response.status_code == 200:
                return True, response.json()
            return False, response.text
            
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования: {e}")
            return False, str(e)
    
    def answer_callback_query(self, callback_query_id, text=None):
        """
        Отвечает на callback query (убирает "часики")
        
        Args:
            callback_query_id (str): ID callback query
            text (str, optional): Текст уведомления
            
        Returns:
            bool: Успешность операции
        """
        try:
            payload = {'callback_query_id': callback_query_id}
            if text:
                payload['text'] = text
            
            response = requests.post(
                f"{self.api_url}/answerCallbackQuery", 
                json=payload, 
                timeout=5
            )
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ Ошибка answer callback: {e}")
            return False


def is_admin(user_id):
    """
    Проверить является ли пользователь администратором
    
    Args:
        user_id (int): Telegram ID пользователя
        
    Returns:
        bool: True если пользователь админ
    """
    import os
    admin_users_str = os.environ.get('ADMIN_USERS', '398232017,1014841100')
    admins = [
        int(uid.strip()) 
        for uid in admin_users_str.split(',') 
        if uid.strip()
    ]
    return user_id in admins


def get_role_emoji(role):
    """
    Возвращает эмодзи для роли пользователя
    
    Args:
        role (str): Роль пользователя
        
    Returns:
        str: Эмодзи соответствующий роли
    """
    return {
        "ДС": "👑",
        "ЗДС": "🎖️",
        "Кладовщик": "👷"
    }.get(role, "👤")


def get_task_type_emoji(task_type):
    """
    Возвращает эмодзи для типа задачи
    
    Args:
        task_type (str): Тип задачи
        
    Returns:
        str: Эмодзи соответствующий типу задачи
    """
    return {
        "Обеды": "🍽️",
        "Уборка": "🧹",
        "Пересчеты": "🔢"
    }.get(task_type, "📋")