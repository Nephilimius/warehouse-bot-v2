#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/report_handlers.py
Хендлеры для работы с отчетами
"""

import logging
from .utils import TelegramAPI, get_task_type_emoji, get_role_emoji
from .database_api import DatabaseAPI
from .keyboards import get_reports_menu

logger = logging.getLogger(__name__)


def handle_reports_menu_text(user_id, api: TelegramAPI):
    """Обработка меню отчетов через текст"""
    
    return api.send_message(
        user_id,
        """📊 *Отчеты и аналитика*

Доступные отчеты:
• Качество работы сотрудников
• Время выполнения задач  
• Статистика по типам задач
• Общая производительность

Выберите тип отчета:""",
        reply_markup=get_reports_menu(),
        parse_mode='Markdown'
    )


def handle_reports_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка меню отчетов через callback"""
    
    return api.edit_message(
        user_id,
        message_id,
        "📊 *Отчеты и аналитика*\n\nДоступные отчеты:\n• Качество работы сотрудников\n• Время выполнения задач\n• Статистика по типам задач\n• Общая производительность\n\nВыберите тип отчета:",
        reply_markup=get_reports_menu()
    )


def handle_quality_report(user_id, message_id, api: TelegramAPI):
    """Обработка отчета по качеству работы"""
    
    quality_data = DatabaseAPI.get_quality_report()
    
    if quality_data:
        message = "⭐ *Отчет по качеству работы*\n\n"
        
        for i, user in enumerate(quality_data[:10]):  # Топ-10
            role_emoji = get_role_emoji(user['role'])
            stars = "⭐" * int(user['avg_rating']) if user['avg_rating'] > 0 else "❌"
            
            message += f"{i+1}. {role_emoji} *@{user['username']}*\n"
            message += f"   Рейтинг: {stars} ({user['avg_rating']:.1f}/5)\n"
            message += f"   Задач: {user['completed_tasks']}/{user['total_tasks']}\n"
            
            if user['avg_time'] > 0:
                message += f"   Время: {user['avg_time']:.0f} мин\n"
            
            message += "\n"
            
            if i >= 9:  # Показываем топ-10
                break
        
        message += f"📊 *Всего проанализировано:* {len(quality_data)} сотрудников"
    else:
        message = "⭐ *Отчет по качеству работы*\n\n❌ Нет данных для анализа\n\n_Выполните несколько задач с оценками для генерации отчета_"
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]},
        parse_mode='Markdown'
    )


def handle_time_report(user_id, message_id, api: TelegramAPI):
    """Обработка отчета по времени выполнения"""
    
    time_data = DatabaseAPI.get_time_report()
    
    if time_data:
        message = "⏱️ *Отчет по времени выполнения*\n\n"
        
        for task_info in time_data:
            type_emoji = get_task_type_emoji(task_info['type'])
            
            message += f"{type_emoji} *{task_info['type']}*\n"
            message += f"   Задач выполнено: {task_info['total_tasks']}\n"
            message += f"   Среднее время: {task_info['avg_time']:.0f} мин\n"
            message += f"   Диапазон: {task_info['min_time']:.0f}-{task_info['max_time']:.0f} мин\n"
            
            if task_info['long_tasks'] > 0:
                message += f"   Долгих задач (>1ч): {task_info['long_tasks']}\n"
            
            message += "\n"
        
        # Общая статистика
        total_tasks = sum(t['total_tasks'] for t in time_data)
        avg_all_time = sum(t['avg_time'] * t['total_tasks'] for t in time_data) / total_tasks if total_tasks > 0 else 0
        
        message += f"📊 *Общая статистика:*\n"
        message += f"Всего задач: {total_tasks}\n"
        message += f"Среднее время: {avg_all_time:.0f} мин"
    else:
        message = "⏱️ *Отчет по времени выполнения*\n\n❌ Нет данных о времени выполнения\n\n_Выполните задачи с указанием времени для генерации отчета_"
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]},
        parse_mode='Markdown'
    )


def handle_tasks_report(user_id, message_id, api: TelegramAPI):
    """Обработка отчета по задачам"""
    
    tasks_data = DatabaseAPI.get_tasks_report()
    
    if tasks_data:
        message = "📋 *Отчет по типам задач*\n\n"
        
        total_all = 0
        completed_all = 0
        
        for task_type, stats in tasks_data.items():
            type_emoji = get_task_type_emoji(task_type)
            
            completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            message += f"{type_emoji} *{task_type}*\n"
            message += f"   Всего: {stats['total']} задач\n"
            message += f"   Выполнено: {stats['completed']} ({completion_rate:.0f}%)\n"
            
            if stats['pending'] > 0:
                message += f"   Ожидают: {stats['pending']}\n"
            
            if stats['in_progress'] > 0:
                message += f"   В работе: {stats['in_progress']}\n"
            
            if stats['avg_rating'] > 0:
                stars = "⭐" * int(stats['avg_rating'])
                message += f"   Качество: {stars} ({stats['avg_rating']:.1f}/5)\n"
            
            message += "\n"
            
            total_all += stats['total']
            completed_all += stats['completed']
        
        # Общая статистика
        overall_completion = (completed_all / total_all * 100) if total_all > 0 else 0
        
        message += f"📊 *Общая эффективность:*\n"
        message += f"Выполнено: {completed_all}/{total_all} ({overall_completion:.0f}%)"
    else:
        message = "📋 *Отчет по типам задач*\n\n❌ Нет данных о задачах\n\n_Создайте задачи для генерации отчета_"
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]},
        parse_mode='Markdown'
    )


def handle_general_report(user_id, message_id, api: TelegramAPI):
    """Обработка общей статистики"""
    
    general_data = DatabaseAPI.get_general_report()
    
    if general_data:
        message = "📈 *Общая статистика системы*\n\n"
        
        # Статистика пользователей
        message += "👥 *Пользователи:*\n"
        for role, count in general_data.get('users', {}).items():
            role_emoji = get_role_emoji(role)
            message += f"   {role_emoji} {role}: {count}\n"
        
        message += f"   📊 Всего: {general_data.get('total_users', 0)}\n\n"
        
        # Статистика задач
        message += "📋 *Задачи:*\n"
        for status, count in general_data.get('tasks', {}).items():
            status_emoji = {"Выполнено": "✅", "Ожидающее": "⏳", "В работе": "🔄"}.get(status, "📋")
            message += f"   {status_emoji} {status}: {count}\n"
        
        message += f"   📊 Всего: {general_data.get('total_tasks', 0)}\n\n"
        
        # Статистика расписания
        if general_data.get('schedule'):
            message += "🗓️ *Расписание:*\n"
            for stype, count in general_data.get('schedule', {}).items():
                type_emoji = get_task_type_emoji(stype)
                message += f"   {type_emoji} {stype}: {count}\n"
            
            message += f"   📊 Всего записей: {general_data.get('total_schedule', 0)}\n\n"
        
        # Качество работы
        if general_data.get('avg_rating', 0) > 0:
            stars = "⭐" * int(general_data['avg_rating'])
            message += f"⭐ *Качество работы:*\n"
            message += f"   Средний рейтинг: {stars} ({general_data['avg_rating']:.1f}/5)\n"
            message += f"   Оценено задач: {general_data.get('rated_tasks', 0)}"
        else:
            message += "⭐ *Качество работы:*\n   ❌ Нет оценок"
    else:
        message = "📈 *Общая статистика*\n\n❌ Нет данных для анализа\n\n_Добавьте пользователей и задачи для генерации статистики_"
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]},
        parse_mode='Markdown'
    )


def handle_report_callback(user_id, message_id, callback_data, api: TelegramAPI):
    """Роутер для callback'ов отчетов"""
    
    if callback_data == 'reports':
        return handle_reports_menu_callback(user_id, message_id, api)
    
    elif callback_data == 'report_quality':
        return handle_quality_report(user_id, message_id, api)
    
    elif callback_data == 'report_time':
        return handle_time_report(user_id, message_id, api)
    
    elif callback_data == 'report_tasks':
        return handle_tasks_report(user_id, message_id, api)
    
    elif callback_data == 'report_general':
        return handle_general_report(user_id, message_id, api)
    
    else:
        return api.edit_message(
            user_id,
            message_id,
            f"❓ Функция `{callback_data}` в разработке",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К отчетам', 'callback_data': 'reports'}]]}
        )
