#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Клавиатуры и меню для Telegram бота
"""

def get_main_menu_keyboard(is_admin=False):
    """Возвращает главное меню"""
    keyboard = [
        [{'text': '🔍 Найти', 'callback_data': 'search'}],
        [{'text': '📄 Задания', 'callback_data': 'tasks'}],
        [{'text': '🗓️ Расписание', 'callback_data': 'schedule'}],
        [{'text': '📊 Отчеты', 'callback_data': 'reports'}],
        [{'text': '🔔 Уведомления', 'callback_data': 'notifications'}],
        [{'text': '👤 Профиль', 'callback_data': 'profile'}],
    ]
    
    if is_admin:
        keyboard.append([{'text': '👑 Администрация', 'callback_data': 'admin'}])
    
    return {'inline_keyboard': keyboard}


def get_reply_keyboard(is_admin=False):
    """Возвращает кнопки меню внизу (ReplyKeyboard)"""
    if is_admin:
        keyboard = [
            ['🔍 Найти', '📄 Задания'],
            ['🗓️ Расписание', '📊 Отчеты'],
            ['🔔 Уведомления', '👤 Профиль'],
            ['👑 Администрация']
        ]
    else:
        keyboard = [
            ['🔍 Найти', '📄 Задания'],
            ['🗓️ Расписание', '📊 Отчеты'],
            ['🔔 Уведомления', '👤 Профиль']
        ]
    
    return {
        'keyboard': keyboard,
        'resize_keyboard': True,
        'one_time_keyboard': False
    }


def get_back_button(callback_data='back_main'):
    """Кнопка назад"""
    return {'inline_keyboard': [[{'text': '◀️ Назад', 'callback_data': callback_data}]]}


def get_tasks_menu(is_admin=False):
    """Меню задач"""
    keyboard = [
        [{'text': '📝 Мои задания', 'callback_data': 'my_tasks'}],
        [{'text': '⏳ Ожидающие', 'callback_data': 'pending_tasks'}],
        [{'text': '✅ Выполненные', 'callback_data': 'completed_tasks'}],
    ]
    
    if is_admin:
        keyboard.append([{'text': '📊 Общая статистика', 'callback_data': 'all_stats'}])
    
    keyboard.append([{'text': '◀️ Назад', 'callback_data': 'back_main'}])
    return {'inline_keyboard': keyboard}


def get_schedule_menu():
    """Меню расписания"""
    return {
        'inline_keyboard': [
            [{'text': '🍽️ Обеды', 'callback_data': 'schedule_meals'}],
            [{'text': '🧹 Уборка', 'callback_data': 'schedule_cleaning'}],
            [{'text': '🔢 Пересчеты', 'callback_data': 'schedule_counting'}],
            [{'text': '◀️ Назад', 'callback_data': 'back_main'}],
        ]
    }


def get_admin_menu():
    """Админское меню"""
    return {
        'inline_keyboard': [
            [{'text': '👥 Список пользователей', 'callback_data': 'admin_users'}],
            [{'text': '📊 Статистика системы', 'callback_data': 'admin_stats'}],
            [{'text': '🗓️ Управление расписанием', 'callback_data': 'admin_schedule'}],
            [{'text': '◀️ Назад', 'callback_data': 'back_main'}],
        ]
    }


def get_admin_schedule_menu():
    """Административное меню управления расписанием"""
    return {
        'inline_keyboard': [
            [{'text': '👀 Просмотр всех записей', 'callback_data': 'admin_schedule_view_all'}],
            [{'text': '🟢 Добавить запись', 'callback_data': 'admin_schedule_add'}],
            [{'text': '🗑️ Удалить записи', 'callback_data': 'admin_schedule_delete'}],
            [{'text': '🍽️ Просмотр обедов', 'callback_data': 'admin_schedule_view_meals'}],
            [{'text': '🧹 Просмотр уборки', 'callback_data': 'admin_schedule_view_cleaning'}],
            [{'text': '🔢 Просмотр пересчетов', 'callback_data': 'admin_schedule_view_counting'}],
            [{'text': '◀️ К админке', 'callback_data': 'admin'}]
        ]
    }


def get_notifications_menu(is_admin=False):
    """Меню уведомлений"""
    keyboard = [
        [{'text': '📱 Мои уведомления', 'callback_data': 'my_notifications'}],
        [{'text': '⚙️ Настройки', 'callback_data': 'notification_settings'}],
    ]
    
    if is_admin:
        keyboard.extend([
            [{'text': '📢 Отправить всем', 'callback_data': 'send_notification_all'}],
            [{'text': '🎯 Отправить по роли', 'callback_data': 'send_notification_role'}],
        ])
    
    keyboard.append([{'text': '◀️ Назад', 'callback_data': 'back_main'}])
    return {'inline_keyboard': keyboard}


def get_reports_menu():
    """Меню отчетов"""
    return {
        'inline_keyboard': [
            [{'text': '⭐ Качество работы', 'callback_data': 'report_quality'}],
            [{'text': '⏱️ Время выполнения', 'callback_data': 'report_time'}],
            [{'text': '📋 По типам задач', 'callback_data': 'report_tasks'}],
            [{'text': '📈 Общая статистика', 'callback_data': 'report_general'}],
            [{'text': '◀️ Назад', 'callback_data': 'back_main'}]
        ]
    }
