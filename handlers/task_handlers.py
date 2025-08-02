#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/task_handlers.py
Хендлеры для работы с задачами
"""

import logging
from .utils import TelegramAPI, get_task_type_emoji, is_admin
import database as db
from .keyboards import get_tasks_menu

logger = logging.getLogger(__name__)


def handle_tasks_menu_text(user_id, api: TelegramAPI):
    """Обработка меню заданий через текст"""
    is_admin_user = is_admin(user_id)
    return api.send_message(
        user_id,
        "📄 *Управление заданиями*\n\nВыберите действие:",
        reply_markup=get_tasks_menu(is_admin_user),
        parse_mode='Markdown'
    )


def handle_tasks_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка меню заданий через callback"""
    is_admin_user = is_admin(user_id)
    return api.edit_message(
        user_id,
        message_id,
        "📄 *Управление заданиями*\n\nВыберите действие:",
        reply_markup=get_tasks_menu(is_admin_user),
        parse_mode='Markdown'
    )


def handle_my_tasks(user_id, message_id, api: TelegramAPI):
    """Обработка просмотра моих задач"""
    tasks = db.get_my_tasks(user_id)
    if tasks:
        message = "📝 *Ваши задания* (последние 10)\n\n"
        for i, task in enumerate(tasks[:10]):
            type_emoji = get_task_type_emoji(task.get('type', ''))
            status = task.get('status', 'Неизвестно')
            status_emoji = {"Выполнено": "✅", "Ожидающее": "⏳", "В работе": "🔄"}.get(status, "📋")
            
            message += f"{i+1}. {status_emoji} *{task.get('type', 'Неизвестно')}* ({status.lower()})\n"
            message += f"   📅 {task.get('when_', 'Не указано')[:16]}\n"
            if task.get('rating') and task.get('rating') > 0:
                message += f"   Оценка: {'⭐' * task['rating']} ({task['rating']}/5)\n"
            message += "\n"
    else:
        message = "📝 *Ваши задания*\n\n❌ У вас пока нет заданий."
    
    return api.edit_message(user_id, message_id, message, reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]}, parse_mode='Markdown')


def handle_pending_tasks(user_id, message_id, api: TelegramAPI):
    """Обработка просмотра ожидающих задач"""
    is_admin_user = is_admin(user_id)
    tasks = db.get_pending_tasks(user_id=None if is_admin_user else user_id)
    title = "⏳ *Все ожидающие задания*" if is_admin_user else "⏳ *Ваши ожидающие задания*"

    if tasks:
        message = f"{title} ({len(tasks)})\n\n"
        for i, task in enumerate(tasks[:10]):
            type_emoji = get_task_type_emoji(task.get('type', ''))
            message += f"{i+1}. {type_emoji} *{task.get('type', 'Неизвестно')}*\n"
            if is_admin_user and task.get('username'):
                message += f"   👤 @{task['username']}\n"
            message += f"   📅 {task.get('when_', 'Не указано')[:16]}\n"
        if len(tasks) > 10: message += f"\n... и еще {len(tasks) - 10} заданий."
    else:
        message = f"{title}\n\n✅ Нет ожидающих заданий."
    
    return api.edit_message(user_id, message_id, message, reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]}, parse_mode='Markdown')


def handle_completed_tasks(user_id, message_id, api: TelegramAPI):
    """Обработка просмотра выполненных задач"""
    is_admin_user = is_admin(user_id)
    tasks = db.get_completed_tasks(user_id=None if is_admin_user else user_id)
    title = "✅ *Все выполненные задания*" if is_admin_user else "✅ *Ваши выполненные задания*"
    
    if tasks:
        message = f"{title} ({len(tasks)})\n\n"
        for i, task in enumerate(tasks[:10]):
            type_emoji = get_task_type_emoji(task.get('type', ''))
            message += f"{i+1}. {type_emoji} *{task.get('type', 'Неизвестно')}*\n"
            if is_admin_user and task.get('username'):
                message += f"   👤 @{task['username']}\n"
            if task.get('rating') and task.get('rating') > 0:
                message += f"   Оценка: {'⭐' * task['rating']}\n"
        if len(tasks) > 10: message += f"\n... и еще {len(tasks) - 10} заданий."
    else:
        message = f"{title}\n\n❌ Нет выполненных заданий."
    
    return api.edit_message(user_id, message_id, message, reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]}, parse_mode='Markdown')


def handle_all_stats(user_id, message_id, api: TelegramAPI):
    """Обработка общей статистики заданий (только для админов)"""
    if not is_admin(user_id): return api.edit_message(user_id, message_id, "❌ У вас нет прав доступа")
    stats = db.get_all_tasks_stats()
    
    if not stats:
        message = "📊 *Общая статистика заданий*\n\n❌ Нет данных для анализа."
    else:
        message = "📊 *Общая статистика заданий*\n\n"
        for task_type, type_stats in stats.items():
            message += f"{get_task_type_emoji(task_type)} *{task_type}*\n"
            for status, s_data in type_stats.items():
                 message += f"   - {status}: {s_data.get('count', 0)}\n"
            message += "\n"

    return api.edit_message(user_id, message_id, message, reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]}, parse_mode='Markdown')


def handle_task_callback(user_id, message_id, query_id, callback_data, api: TelegramAPI):
    """Роутер для callback'ов задач"""
    api.answer_callback_query(query_id)

    if callback_data == 'tasks_my':
        return handle_my_tasks(user_id, message_id, api)
    
    elif callback_data == 'tasks_pending':
        return handle_pending_tasks(user_id, message_id, api)
    
    elif callback_data == 'tasks_completed':
        return handle_completed_tasks(user_id, message_id, api)
    
    elif callback_data == 'tasks_stats_all':
        return handle_all_stats(user_id, message_id, api)
    
    # Если мы здесь, значит это 'tasks' - главное меню раздела
    return handle_tasks_menu_callback(user_id, message_id, api)
