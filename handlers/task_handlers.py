#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/task_handlers.py
Хендлеры для работы с задачами
"""

import logging
from .utils import TelegramAPI, get_task_type_emoji
from .database_api import db
from .keyboards import get_tasks_menu, get_back_button

logger = logging.getLogger(__name__)


def handle_tasks_menu_text(user_id, api: TelegramAPI):
    """Обработка меню заданий через текст"""
    
    is_admin = db.is_admin(user_id)
    
    return api.send_message(
        user_id,
        """📄 *Управление заданиями*

Выберите действие:""",
        reply_markup=get_tasks_menu(is_admin),
        parse_mode='Markdown'
    )


def handle_tasks_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка меню заданий через callback"""
    
    is_admin = db.is_admin(user_id)
    
    return api.edit_message(
        user_id,
        message_id,
        "📄 *Управление заданиями*\n\nВыберите действие:",
        reply_markup=get_tasks_menu(is_admin)
    )


def handle_my_tasks(user_id, message_id, api: TelegramAPI):
    """Обработка просмотра моих задач"""
    
    tasks = db.get_my_tasks(user_id)
    
    if tasks:
        message = "📝 *Ваши задания* (последние 10)\n\n"
        
        for i, task in enumerate(tasks[:10]):
            type_emoji = get_task_type_emoji(task.get('type', ''))
            
            message += f"{i+1}. {type_emoji} *{task.get('type', 'Неизвестно')}*\n"
            message += f"📅 {task.get('when_', 'Не указано')[:16]}\n"
            
            if task.get('description'):
                desc = task['description'][:50] + "..." if len(task['description']) > 50 else task['description']
                message += f"📝 {desc}\n"
            
            status = task.get('status', 'Неизвестно')
            status_emoji = {"Выполнено": "✅", "Ожидающее": "⏳", "В работе": "🔄"}.get(status, "📋")
            message += f"{status_emoji} {status}\n"
            
            if task.get('rating'):
                stars = "⭐" * task['rating']
                message += f"{stars} ({task['rating']}/5)\n"
            
            message += "\n"
    else:
        message = "📝 *Ваши задания*\n\n❌ У вас пока нет заданий"
    
    return api.edit_message(
        user_id,
        message_id,
        message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]},
        parse_mode='Markdown'
    )


def handle_pending_tasks(user_id, message_id, api: TelegramAPI):
    """Обработка просмотра ожидающих задач"""
    
    is_admin = db.is_admin(user_id)
    
    if is_admin:
        tasks = db.get_pending_tasks()  # Все ожидающие
        title = "⏳ *Все ожидающие задания*"
    else:
        tasks = db.get_pending_tasks(user_id)  # Только свои
        title = "⏳ *Ваши ожидающие задания*"
    
    if tasks:
        message = f"{title}\n\n"
        
        for i, task in enumerate(tasks[:10]):
            type_emoji = get_task_type_emoji(task.get('type', ''))
            
            message += f"{i+1}. {type_emoji} *{task.get('type', 'Неизвестно')}*\n"
            message += f"📅 {task.get('when_', 'Не указано')[:16]}\n"
            
            if is_admin and task.get('username'):
                message += f"👤 @{task['username']}\n"
            
            if task.get('description'):
                desc = task['description'][:50] + "..." if len(task['description']) > 50 else task['description']
                message += f"📝 {desc}\n"
            
            message += "\n"
        
        if len(tasks) > 10:
            message += f"... и еще {len(tasks) - 10} заданий"
    else:
        message = f"{title}\n\n✅ Нет ожидающих заданий"
    
    return api.edit_message(
        user_id,
        message_id,
        message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]},
        parse_mode='Markdown'
    )


def handle_completed_tasks(user_id, message_id, api: TelegramAPI):
    """Обработка просмотра выполненных задач"""
    
    is_admin = db.is_admin(user_id)
    
    if is_admin:
        tasks = db.get_completed_tasks()  # Все выполненные
        title = "✅ *Все выполненные задания*"
    else:
        tasks = db.get_completed_tasks(user_id)  # Только свои
        title = "✅ *Ваши выполненные задания*"
    
    if tasks:
        message = f"{title}\n\n"
        
        for i, task in enumerate(tasks[:10]):
            type_emoji = get_task_type_emoji(task.get('type', ''))
            
            message += f"{i+1}. {type_emoji} *{task.get('type', 'Неизвестно')}*\n"
            message += f"📅 {task.get('when_', 'Не указано')[:16]}\n"
            
            if is_admin and task.get('username'):
                message += f"👤 @{task['username']}\n"
            
            if task.get('description'):
                desc = task['description'][:50] + "..." if len(task['description']) > 50 else task['description']
                message += f"📝 {desc}\n"
            
            if task.get('rating'):
                stars = "⭐" * task['rating']
                message += f"Оценка: {stars} ({task['rating']}/5)\n"
            
            if task.get('time_spent'):
                message += f"⏱️ Время: {task['time_spent']} мин\n"
            
            message += "\n"
        
        if len(tasks) > 10:
            message += f"... и еще {len(tasks) - 10} заданий"
    else:
        message = f"{title}\n\n❌ Нет выполненных заданий"
    
    return api.edit_message(
        user_id,
        message_id,
        message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]},
        parse_mode='Markdown'
    )


def handle_all_stats(user_id, message_id, api: TelegramAPI):
    """Обработка общей статистики заданий (только для админов)"""
    
    if not db.is_admin(user_id):
        return api.edit_message(
            user_id,
            message_id,
            "❌ У вас нет прав доступа"
        )
    
    all_pending = db.get_pending_tasks()
    all_completed = db.get_completed_tasks()
    
    # Группируем по типам
    pending_by_type = {}
    completed_by_type = {}
    
    for task in all_pending:
        task_type = task.get('type', 'Неизвестно')
        pending_by_type[task_type] = pending_by_type.get(task_type, 0) + 1
    
    for task in all_completed:
        task_type = task.get('type', 'Неизвестно')
        completed_by_type[task_type] = completed_by_type.get(task_type, 0) + 1
    
    message = "📊 *Общая статистика заданий*\n\n"
    
    # Статистика по типам
    all_types = set(list(pending_by_type.keys()) + list(completed_by_type.keys()))
    
    for task_type in all_types:
        type_emoji = get_task_type_emoji(task_type)
        pending_count = pending_by_type.get(task_type, 0)
        completed_count = completed_by_type.get(task_type, 0)
        total = pending_count + completed_count
        
        message += f"{type_emoji} *{task_type}*\n"
        message += f"   ⏳ Ожидающих: {pending_count}\n"
        message += f"   ✅ Выполненных: {completed_count}\n"
        message += f"   📊 Всего: {total}\n\n"
    
    # Общая статистика
    total_pending = len(all_pending)
    total_completed = len(all_completed)
    total_all = total_pending + total_completed
    
    message += f"📈 *Общие итоги:*\n"
    message += f"⏳ Ожидающих: {total_pending}\n"
    message += f"✅ Выполненных: {total_completed}\n"
    message += f"📊 Всего заданий: {total_all}"
    
    return api.edit_message(
        user_id,
        message_id,
        message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]},
        parse_mode='Markdown'
    )


def handle_task_callback(user_id, message_id, callback_data, api: TelegramAPI):
    """Роутер для callback'ов задач"""
    
    if callback_data == 'tasks':
        return handle_tasks_menu_callback(user_id, message_id, api)
    
    elif callback_data == 'my_tasks':
        return handle_my_tasks(user_id, message_id, api)
    
    elif callback_data == 'pending_tasks':
        return handle_pending_tasks(user_id, message_id, api)
    
    elif callback_data == 'completed_tasks':
        return handle_completed_tasks(user_id, message_id, api)
    
    elif callback_data == 'all_stats':
        return handle_all_stats(user_id, message_id, api)
    
    else:
        return api.edit_message(
            user_id,
            message_id,
            f"❓ Функция `{callback_data}` в разработке",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]}
        )