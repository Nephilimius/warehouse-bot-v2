#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/admin_handlers.py
Хендлеры для администраторских функций
"""

import logging
from .utils import TelegramAPI, get_role_emoji, get_task_type_emoji
from .database_api import DatabaseAPI
from .keyboards import get_admin_menu, get_admin_schedule_menu
from .main_handlers import set_user_state, get_user_data, set_user_data

logger = logging.getLogger(__name__)


def handle_admin_menu_text(user_id, api: TelegramAPI):
    """Обработка админского меню через текст"""
    
    return api.send_message(
        user_id,
        """👑 *Панель администратора*

Выберите действие:""",
        reply_markup=get_admin_menu(),
        parse_mode='Markdown'
    )


def handle_admin_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка админского меню через callback"""
    
    return api.edit_message(
        user_id,
        message_id,
        "👑 *Панель администратора*\n\nВыберите действие:",
        reply_markup=get_admin_menu()
    )


def handle_admin_users(user_id, message_id, api: TelegramAPI):
    """Обработка списка пользователей"""
    
    users = DatabaseAPI.get_all_users()
    
    if users:
        message = f"👥 *Список пользователей* ({len(users)})\n\n"
        
        for i, user in enumerate(users[:10]):  # Показываем первых 10
            role_emoji = get_role_emoji(user['role'])
            message += f"{i+1}. {role_emoji} @{user['username']} - {user['role']}\n"
            message += f"   📋 Задач: {user['tasks_count']}, ⭐ {user['average_rating']:.1f}\n\n"
        
        if len(users) > 10:
            message += f"... и еще {len(users) - 10} пользователей"
    else:
        message = "👥 *Список пользователей*\n\n❌ Пользователи не найдены"
    
    return api.edit_message(
        user_id,
        message_id,
        message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К админке', 'callback_data': 'admin'}]]},
        parse_mode='Markdown'
    )


def handle_admin_stats(user_id, message_id, api: TelegramAPI):
    """Обработка статистики системы"""
    
    users = DatabaseAPI.get_all_users()
    pending_tasks = DatabaseAPI.get_pending_tasks()
    completed_tasks = DatabaseAPI.get_completed_tasks()
    
    # Подсчитываем статистику по ролям
    role_stats = {}
    for user in users:
        role = user.get('role', 'Неизвестно')
        role_stats[role] = role_stats.get(role, 0) + 1
    
    message = f"📊 *Статистика системы*\n\n"
    message += f"👥 *Пользователи:*\n"
    for role, count in role_stats.items():
        role_emoji = get_role_emoji(role)
        message += f"{role_emoji} {role}: {count}\n"
    
    message += f"\n📋 *Задания:*\n"
    message += f"⏳ Ожидающих: {len(pending_tasks)}\n"
    message += f"✅ Выполненных: {len(completed_tasks)}\n"
    message += f"📊 Всего: {len(pending_tasks) + len(completed_tasks)}"
    
    return api.edit_message(
        user_id,
        message_id,
        message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К админке', 'callback_data': 'admin'}]]},
        parse_mode='Markdown'
    )


def handle_admin_schedule_menu(user_id, message_id, api: TelegramAPI):
    """Обработка админского меню расписания"""
    
    return api.edit_message(
        user_id,
        message_id,
        "🗓️ *Управление расписанием*\n\nВыберите действие:",
        reply_markup=get_admin_schedule_menu(),
        parse_mode='Markdown'
    )


def handle_admin_schedule_view_all(user_id, message_id, api: TelegramAPI):
    """Просмотр всех записей расписания"""
    
    message = "👀 *Все записи расписания*\n\n"
    total = 0
    all_items = []
    
    # Собираем все записи
    for stype in ['Обеды', 'Уборка', 'Пересчеты']:
        items = DatabaseAPI.get_schedule_by_type(stype)
        if items:
            for item in items:
                item['type'] = stype
                all_items.append(item)
            total += len(items)
    
    if total == 0:
        message += "❌ Нет записей в расписании"
    else:
        # Сортируем по дате
        all_items.sort(key=lambda x: x.get('date', ''))
        
        # Показываем детали (первые 10 записей)
        for i, item in enumerate(all_items[:10]):
            emoji = get_task_type_emoji(item['type'])
            time_str = f"{item['start_time']}-{item['end_time']}"
            if time_str == "00:00-23:59":
                time_str = "Весь день"
            
            message += f"{i+1}. {emoji} *{item['type']}*\n"
            message += f"   📅 {item['date']} {time_str}\n"
            message += f"   👤 @{item['username']}\n"
            if 'id' in item:
                message += f"   🆔 {item['id'][:8]}...\n"
            message += "\n"
        
        if len(all_items) > 10:
            message += f"... и еще {len(all_items) - 10} записей\n"
        
        message += f"\n📊 *Всего записей:* {total}"
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup=get_admin_schedule_menu(),
        parse_mode='Markdown'
    )


def handle_admin_schedule_add(user_id, message_id, api: TelegramAPI):
    """Добавление записи в расписание"""
    
    # Переходим к выбору типа записи
    keyboard = [
        [{'text': '🍽️ Добавить обед', 'callback_data': 'admin_add_meals'}],
        [{'text': '🧹 Добавить уборку', 'callback_data': 'admin_add_cleaning'}],
        [{'text': '🔢 Добавить пересчет', 'callback_data': 'admin_add_counting'}],
        [{'text': '◀️ Назад', 'callback_data': 'admin_schedule'}]
    ]
    
    return api.edit_message(
        user_id, message_id,
        "🟢 *Добавление записи в расписание*\n\nВыберите тип задания:",
        reply_markup={'inline_keyboard': keyboard},
        parse_mode='Markdown'
    )


def handle_admin_add_task_type(user_id, message_id, callback_data, api: TelegramAPI):
    """Обработка выбора типа для добавления"""
    
    # Определяем тип
    type_map = {
        'admin_add_meals': 'Обеды',
        'admin_add_cleaning': 'Уборка',
        'admin_add_counting': 'Пересчеты'
    }
    
    task_type = type_map.get(callback_data)
    if not task_type:
        return api.edit_message(user_id, message_id, "❌ Неизвестный тип")
    
    # Сохраняем тип в user_data
    user_data = get_user_data()
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['creating_schedule'] = {'type': task_type}
    set_user_state(user_id, 'admin_schedule_select_user')
    
    # Получаем список пользователей
    users = DatabaseAPI.get_all_users()
    if not users:
        return api.edit_message(user_id, message_id, "❌ Нет пользователей")
    
    # Формируем кнопки выбора пользователей
    keyboard = []
    for user in users[:10]:  # Первые 10 пользователей
        role_emoji = get_role_emoji(user.get('role', ''))
        keyboard.append([{
            'text': f"{role_emoji} @{user['username']}", 
            'callback_data': f'admin_select_user_{user["telegram_id"]}'
        }])
    
    keyboard.append([{'text': '❌ Отмена', 'callback_data': 'admin_schedule'}])
    
    type_emoji = get_task_type_emoji(task_type)
    
    return api.edit_message(
        user_id, message_id,
        f"👥 *Добавление: {type_emoji} {task_type}*\n\nВыберите исполнителя:",
        reply_markup={'inline_keyboard': keyboard},
        parse_mode='Markdown'
    )


def handle_admin_select_user(user_id, message_id, callback_data, api: TelegramAPI):
    """Обработка выбора пользователя"""
    
    # Проверяем что создаем расписание
    user_data = get_user_data()
    if (user_id not in user_data or 
        'creating_schedule' not in user_data[user_id]):
        return api.edit_message(user_id, message_id, "❌ Данные потеряны, начните заново")
    
    # Сохраняем выбранного пользователя
    selected_user_id = callback_data.replace('admin_select_user_', '')
    user_data[user_id]['creating_schedule']['assigned_to'] = selected_user_id
    
    # Найдем username
    users = DatabaseAPI.get_all_users()
    selected_user = next((u for u in users if u['telegram_id'] == selected_user_id), None)
    
    if selected_user:
        user_data[user_id]['creating_schedule']['assigned_username'] = selected_user['username']
        set_user_state(user_id, 'admin_schedule_input_date')
        
        task_type = user_data[user_id]['creating_schedule']['type']
        type_emoji = get_task_type_emoji(task_type)
        
        return api.edit_message(
            user_id, message_id,
            f"📅 *Дата выполнения*\n\n"
            f"Задание: {type_emoji} {task_type}\n"
            f"Исполнитель: @{selected_user['username']}\n\n"
            f"Введите дату в любом формате:\n"
            f"• `сегодня` или `завтра`\n"
            f"• `26.07` или `26.07.2025`\n"
            f"• `27.07` или `2025-07-27`\n\n"
            f"Или напишите /cancel для отмены",
            parse_mode='Markdown'
        )
    else:
        return api.edit_message(user_id, message_id, "❌ Пользователь не найден")


def handle_admin_callback(user_id, message_id, callback_data, api: TelegramAPI):
    """Роутер для админских callback'ов"""
    
    if callback_data == 'admin':
        return handle_admin_menu_callback(user_id, message_id, api)
    
    elif callback_data == 'admin_users':
        return handle_admin_users(user_id, message_id, api)
    
    elif callback_data == 'admin_stats':
        return handle_admin_stats(user_id, message_id, api)
    
    elif callback_data == 'admin_schedule':
        return handle_admin_schedule_menu(user_id, message_id, api)
    
    elif callback_data == 'admin_schedule_view_all':
        return handle_admin_schedule_view_all(user_id, message_id, api)
    
    elif callback_data == 'admin_schedule_add':
        return handle_admin_schedule_add(user_id, message_id, api)
    
    elif callback_data.startswith('admin_add_'):
        return handle_admin_add_task_type(user_id, message_id, callback_data, api)
    
    elif callback_data.startswith('admin_select_user_'):
        return handle_admin_select_user(user_id, message_id, callback_data, api)
    
    else:
        return api.edit_message(
            user_id,
            message_id,
            f"❓ Админская функция `{callback_data}` в разработке",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К админке', 'callback_data': 'admin'}]]}
        )
