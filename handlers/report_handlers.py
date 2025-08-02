#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/report_handlers.py
Хендлеры для работы с отчетами
"""

import logging
from .utils import TelegramAPI, get_task_type_emoji, get_role_emoji
import database as db
from .keyboards import get_reports_menu

logger = logging.getLogger(__name__)


def handle_reports_menu_text(user_id, api: TelegramAPI):
    """Обработка меню отчетов через текст (с Reply кнопки)"""
    return api.send_message(
        user_id,
        "📊 *Отчеты и аналитика*\n\nВыберите тип отчета:",
        reply_markup=get_reports_menu(),
        parse_mode='Markdown'
    )


def handle_reports_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка меню отчетов через callback (с Inline кнопки)"""
    return api.edit_message(
        user_id,
        message_id,
        "📊 *Отчеты и аналитика*\n\nВыберите тип отчета:",
        reply_markup=get_reports_menu(),
        parse_mode='Markdown'
    )


def handle_quality_report(user_id, message_id, api: TelegramAPI):
    """Обработка отчета по качеству работы"""
    
    quality_data = db.get_quality_report()
    
    if quality_data:
        message = "⭐ *Отчет по качеству работы*\n\n"
        for i, user in enumerate(quality_data[:10]):
            role_emoji = get_role_emoji(user['role'])
            stars = "⭐" * int(user.get('avg_rating', 0)) if user.get('avg_rating', 0) > 0 else "❌"
            
            # Используем Markdown-совместимое форматирование для никнеймов
            username = user['username'].replace('_', '\\_')
            message += f"{i+1}. {role_emoji} *@{username}*\n"
            message += f"   Рейтинг: {stars} ({user.get('avg_rating', 0):.1f}/5)\n"
            message += f"   Задач: {user.get('completed_tasks', 0)}/{user.get('total_tasks', 0)}\n\n"
        
        message += f"📊 *Всего проанализировано:* {len(quality_data)} сотрудников"
    else:
        message = "⭐ *Отчет по качеству работы*\n\n❌ Нет данных для анализа."
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]},
        parse_mode='Markdown'
    )


def handle_time_report(user_id, message_id, api: TelegramAPI):
    """Обработка отчета по времени выполнения"""
    
    time_data = db.get_time_report()
    
    if time_data:
        message = "⏱️ *Отчет по времени выполнения*\n\n"
        for task_info in time_data:
            type_emoji = get_task_type_emoji(task_info['type'])
            
            message += f"{type_emoji} *{task_info['type']}*\n"
            message += f"   Среднее время: {task_info.get('avg_time', 0):.0f} мин\n"
            message += f"   Задач выполнено: {task_info.get('total_tasks', 0)}\n\n"
    else:
        message = "⏱️ *Отчет по времени выполнения*\n\n❌ Нет данных о времени выполнения."
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]},
        parse_mode='Markdown'
    )


def handle_tasks_report(user_id, message_id, api: TelegramAPI):
    """Обработка отчета по задачам"""
    
    tasks_data = db.get_tasks_report()
    
    if tasks_data:
        message = "📋 *Отчет по типам задач*\n\n"
        for task_type, stats in tasks_data.items():
            type_emoji = get_task_type_emoji(task_type)
            # Добавлена проверка на деление на ноль
            total = stats.get('total', 0)
            completed = stats.get('completed', 0)
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            message += f"{type_emoji} *{task_type}* ({completion_rate:.0f}% выполнено)\n"
            message += f"   Всего: {total}, Выполнено: {completed}\n\n"
    else:
        message = "📋 *Отчет по типам задач*\n\n❌ Нет данных о задачах."
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]},
        parse_mode='Markdown'
    )


def handle_general_report(user_id, message_id, api: TelegramAPI):
    """Обработка общей статистики"""
    
    general_data = db.get_general_report()
    
    if general_data:
        message = "📈 *Общая статистика системы*\n\n"
        
        message += "👥 *Пользователи:*\n"
        for role, count in general_data.get('users', {}).items():
            role_emoji = get_role_emoji(role)
            message += f"   {role_emoji} {role}: {count}\n"
        
        message += f"\n📋 *Задачи:*\n"
        for status, count in general_data.get('tasks', {}).items():
            status_emoji = {"Выполнено": "✅", "Ожидающее": "⏳", "В работе": "🔄"}.get(status, "📋")
            message += f"   {status_emoji} {status}: {count}\n"
        
        if general_data.get('avg_rating', 0) > 0:
            stars = "⭐" * int(general_data['avg_rating'])
            message += f"\n⭐ *Средний рейтинг по задачам:*\n"
            message += f"   {stars} ({general_data['avg_rating']:.1f}/5)"
    else:
        message = "📈 *Общая статистика*\n\n❌ Нет данных для анализа."
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]},
        parse_mode='Markdown'
    )


# --- ИСПРАВЛЕНИЕ ЗДЕСЬ: добавлен недостающий параметр query_id ---
def handle_report_callback(user_id, message_id, query_id, callback_data, api: TelegramAPI):
    """Роутер для callback'ов отчетов"""
    
    # Отвечаем на callback, чтобы убрать "часики"
    api.answer_callback_query(query_id)
    
    if callback_data == 'report_quality':
        return handle_quality_report(user_id, message_id, api)
    
    elif callback_data == 'report_time':
        return handle_time_report(user_id, message_id, api)
    
    elif callback_data == 'report_tasks':
        return handle_tasks_report(user_id, message_id, api)
    
    elif callback_data == 'report_general':
        return handle_general_report(user_id, message_id, api)
    
    else:
        # Заглушка на случай неизвестного callback'а
        return api.edit_message(
            user_id,
            message_id,
            f"❓ Функция отчетов `{callback_data}` в разработке",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]}
        )