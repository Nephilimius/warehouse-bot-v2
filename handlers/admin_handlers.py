#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/admin_handlers.py
Хендлеры для администраторских функций
"""

import logging
from .utils import TelegramAPI, get_role_emoji, get_task_type_emoji
import database as db
from .keyboards import get_admin_menu, get_admin_schedule_menu

logger = logging.getLogger(__name__)


def handle_admin_menu_text(user_id, api: TelegramAPI):
    """Обработка админского меню через текст"""
    return api.send_message(
        user_id,
        "👑 *Панель администратора*\n\nВыберите действие:",
        reply_markup=get_admin_menu(),
        parse_mode='Markdown'
    )


def handle_admin_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка админского меню через callback"""
    return api.edit_message(
        user_id,
        message_id,
        "👑 *Панель администратора*\n\nВыберите действие:",
        reply_markup=get_admin_menu(),
        parse_mode='Markdown'
    )


def handle_admin_users(user_id, message_id, api: TelegramAPI):
    """Обработка списка пользователей"""
    users = db.get_all_users()
    if users:
        message = f"👥 *Список пользователей* ({len(users)})\n\n"
        for i, user in enumerate(users[:10]):
            role_emoji = get_role_emoji(user['role'])
            message += f"{i+1}. {role_emoji} @{user['username']} - {user['role']}\n"
            message += f"   📋 Задач: {user.get('tasks_count', 0)}, ⭐ {user.get('average_rating', 0.0):.1f}\n\n"
        if len(users) > 10:
            message += f"... и еще {len(users) - 10} пользователей."
    else:
        message = "👥 *Список пользователей*\n\n❌ Пользователи не найдены."
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К админке', 'callback_data': 'admin'}]]},
        parse_mode='Markdown'
    )


def handle_admin_stats(user_id, message_id, api: TelegramAPI):
    """Обработка статистики системы"""
    stats = db.get_system_stats()
    message = "📊 *Статистика системы*\n\n"
    if stats:
        message += "👥 *Пользователи:*\n"
        for role, count in stats.get('users', {}).items():
            message += f"   {get_role_emoji(role)} {role}: {count}\n"
        
        message += "\n📋 *Задания:*\n"
        for status, count in stats.get('tasks', {}).items():
            message += f"   {status}: {count}\n"
    else:
        message += "❌ Не удалось загрузить статистику."

    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К админке', 'callback_data': 'admin'}]]},
        parse_mode='Markdown'
    )


def handle_admin_schedule_menu(user_id, message_id, api: TelegramAPI):
    """Обработка админского меню расписания"""
    return api.edit_message(
        user_id, message_id,
        "🗓️ *Управление расписанием*\n\nВыберите действие:",
        reply_markup=get_admin_schedule_menu(),
        parse_mode='Markdown'
    )

def handle_admin_schedule_view_all(user_id, message_id, api: TelegramAPI):
    """Просмотр всех записей расписания"""
    all_items = db.get_all_schedule_items()
    if not all_items:
        message = "👀 *Все записи расписания*\n\n❌ Нет активных записей в расписании."
    else:
        message = f"👀 *Все записи расписания* ({len(all_items)})\n\n"
        for i, item in enumerate(all_items[:10]):
            emoji = get_task_type_emoji(item['type'])
            time_str = f"{item['start_time']}-{item['end_time']}"
            if time_str == "00:00-23:59": time_str = "Весь день"
            message += f"{i+1}. {emoji} *{item['type']}* на {item['date']}\n"
            message += f"   @{item['username']} ({time_str})\n"
        if len(all_items) > 10:
            message += f"\n... и еще {len(all_items) - 10} записей."
            
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К упр. расписанием', 'callback_data': 'admin_schedule'}]]},
        parse_mode='Markdown'
    )

def handle_admin_schedule_add(user_id, message_id, api: TelegramAPI):
    """Добавление записи в расписание"""
    keyboard = [
        [{'text': '🍽️ Обеды', 'callback_data': 'admin_schedule_add_Обеды'}],
        [{'text': '🧹 Уборка', 'callback_data': 'admin_schedule_add_Уборка'}],
        [{'text': '🔢 Пересчеты', 'callback_data': 'admin_schedule_add_Пересчеты'}],
        [{'text': '◀️ Назад', 'callback_data': 'admin_schedule'}]
    ]
    return api.edit_message(
        user_id, message_id,
        "🟢 *Добавление записи*\n\nВыберите тип задания:",
        reply_markup={'inline_keyboard': keyboard},
        parse_mode='Markdown'
    )

def handle_admin_callback(user_id, message_id, query_id, callback_data, api: TelegramAPI):
    """Роутер для админских callback'ов"""
    api.answer_callback_query(query_id)

    # Главное меню админки
    if callback_data == 'admin':
        return handle_admin_menu_callback(user_id, message_id, api)
    
    # Пользователи и статистика
    elif callback_data == 'admin_users':
        return handle_admin_users(user_id, message_id, api)
    elif callback_data == 'admin_stats':
        return handle_admin_stats(user_id, message_id, api)
        
    # Меню управления расписанием
    elif callback_data == 'admin_schedule':
        return handle_admin_schedule_menu(user_id, message_id, api)
    elif callback_data == 'admin_schedule_view_all':
        return handle_admin_schedule_view_all(user_id, message_id, api)
    elif callback_data == 'admin_schedule_add':
        return handle_admin_schedule_add(user_id, message_id, api)

    # Процесс создания записи в расписании
    elif callback_data.startswith('admin_schedule_add_'):
        task_type = callback_data.replace('admin_schedule_add_', '')
        db.set_user_state(user_id, 'admin_schedule_select_user', {'creating_schedule': {'type': task_type}})
        
        users = db.get_all_users()
        if not users: return api.edit_message(user_id, message_id, "❌ Нет пользователей")
        
        keyboard = [[{'text': f"{get_role_emoji(u.get('role', ''))} @{u['username']}", 'callback_data': f"admin_schedule_select_{u['telegram_id']}"}] for u in users[:15]]
        keyboard.append([{'text': '❌ Отмена', 'callback_data': 'admin_schedule'}])
        
        return api.edit_message(user_id, message_id, f"👥 *Добавление: {task_type}*\n\nВыберите исполнителя:", reply_markup={'inline_keyboard': keyboard}, parse_mode='Markdown')

    elif callback_data.startswith('admin_schedule_select_'):
        state, data = db.get_user_state(user_id)
        if not state.startswith('admin_schedule_'): return api.edit_message(user_id, message_id, "❌ Истек срок действия")

        selected_user_id = callback_data.replace('admin_schedule_select_', '')
        data['creating_schedule']['assigned_to'] = selected_user_id
        
        users = db.get_all_users()
        selected_user = next((u for u in users if str(u['telegram_id']) == str(selected_user_id)), None)
        if not selected_user: return api.edit_message(user_id, message_id, "❌ Пользователь не найден")

        data['creating_schedule']['assigned_username'] = selected_user['username']
        db.set_user_state(user_id, 'admin_schedule_input_date', data)
        
        return api.edit_message(user_id, message_id, f"📅 *Дата выполнения*\n\nЗадание: {data['creating_schedule']['type']}\nИсполнитель: @{selected_user['username']}\n\nВведите дату (например, `сегодня`, `завтра`, `31.12`):", parse_mode='Markdown')
