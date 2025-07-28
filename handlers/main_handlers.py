#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/main_handlers.py
Основные хендлеры команд и текстовых сообщений
"""

import logging
from .utils import TelegramAPI
from .database_api import DatabaseAPI
from .keyboards import get_main_menu_keyboard, get_reply_keyboard, get_back_button

logger = logging.getLogger(__name__)

# Глобальные состояния пользователей
user_states = {}
user_data = {}


def handle_start_command(user_id, username, first_name, api: TelegramAPI):
    """Обработка команды /start"""
    
    user_states[user_id] = 'main'
    
    # Получаем пользователя из базы
    user = DatabaseAPI.get_or_create_user(user_id, username)
    role = user.get('role', 'Кладовщик') if user else 'Кладовщик'
    is_admin = DatabaseAPI.is_admin(user_id)
    
    welcome_text = f"""🤖 *Добро пожаловать, {first_name}!*

*Ваша роль:* {role}
{'👑 У вас есть права администратора!' if is_admin else ''}

Выберите раздел из меню ниже:"""
    
    # Отправляем с кнопками внизу
    return api.send_message(
        user_id,
        welcome_text,
        reply_markup=get_reply_keyboard(is_admin)
    )


def handle_cancel_command(user_id, api: TelegramAPI):
    """Обработка команды /cancel"""
    
    user_states[user_id] = 'main'
    is_admin = DatabaseAPI.is_admin(user_id)
    
    # Очищаем состояния
    if user_id in user_data and 'creating_schedule' in user_data[user_id]:
        del user_data[user_id]['creating_schedule']
    
    return api.send_message(
        user_id,
        "❌ Операция отменена. Используйте кнопки меню ниже.",
        reply_markup=get_reply_keyboard(is_admin)
    )


def handle_search_text(user_id, text, api: TelegramAPI):
    """Обработка поиска пользователя"""
    
    user_states[user_id] = 'main'
    
    # Убираем @ если есть
    username = text.replace("@", "")
    
    # Поиск пользователя (пока заглушка)
    users = DatabaseAPI.get_all_users()
    found_user = None
    
    for user in users:
        if user.get('username', '').lower() == username.lower():
            found_user = user
            break
    
    if found_user:
        from .utils import get_role_emoji
        
        role_emoji = get_role_emoji(found_user['role'])
        
        message = f"""🔍 *Результат поиска*

👤 *@{found_user['username']}*
{role_emoji} Роль: {found_user['role']}
📋 Всего задач: {found_user.get('tasks_count', 0)}
⭐ Средний рейтинг: {found_user.get('average_rating', 0):.1f}
🆔 ID: {found_user['telegram_id']}"""
    else:
        message = f"🔍 *Результат поиска*\n\n❌ Пользователь `@{username}` не найден"
    
    is_admin = DatabaseAPI.is_admin(user_id)
    return api.send_message(
        user_id,
        message,
        reply_markup=get_main_menu_keyboard(is_admin)
    )


def handle_profile_text(user_id, api: TelegramAPI):
    """Обработка профиля через текст"""
    
    # Получаем данные пользователя из базы
    user = DatabaseAPI.get_or_create_user(user_id)
    
    if user:
        is_admin = DatabaseAPI.is_admin(user_id)
        admin_status = "\n👑 *Статус:* Администратор" if is_admin else ""
        
        message = f"""👤 *Ваш профиль*

📱 *Username:* @{user.get('username', 'Не указан')}
🎭 *Роль:* {user.get('role', 'Не указана')}{admin_status}
📋 *Заданий выполнено:* {user.get('tasks_count', 0)}
⭐ *Средний рейтинг:* {user.get('average_rating', 0):.1f}
💎 *Качество работы:* {user.get('quality_score', 0):.1f}
🆔 *ID:* {user_id}"""
    else:
        message = f"""👤 *Профиль*

❌ Ошибка получения данных
🆔 *ID:* {user_id}"""
    
    return api.send_message(
        user_id,
        message,
        reply_markup=get_back_button(),
        parse_mode='Markdown'
    )


def handle_text_message(user_id, username, text, api: TelegramAPI):
    """Главный обработчик текстовых сообщений"""
    
    is_admin = DatabaseAPI.is_admin(user_id)
    
    # Команды
    if text == "/start":
        return handle_start_command(user_id, username, "Пользователь", api)
    
    elif text == "/cancel":
        return handle_cancel_command(user_id, api)
    
    # Обработка кнопок меню
    elif '🔍 Найти' in text or text == 'Найти':
        user_states[user_id] = 'search'
        return api.send_message(
            user_id,
            """🔍 *Поиск и аналитика пользователя*

Введите username для поиска:""",
            parse_mode='Markdown'
        )
    
    elif '📄 Задания' in text or text == 'Задания':
        from .task_handlers import handle_tasks_menu_text
        return handle_tasks_menu_text(user_id, api)
    
    elif '🗓️ Расписание' in text or text == 'Расписание':
        from .shedule_handlers import handle_schedule_menu_text
        return handle_schedule_menu_text(user_id, api)
    
    elif '📊 Отчеты' in text or text == 'Отчеты':
        from .report_handlers import handle_reports_menu_text
        return handle_reports_menu_text(user_id, api)
    
    elif '🔔 Уведомления' in text or text == 'Уведомления':
        from .notification_handlers import handle_notifications_menu_text
        return handle_notifications_menu_text(user_id, api)
    
    elif '👤 Профиль' in text or text == 'Профиль':
        return handle_profile_text(user_id, api)
    
    elif '👑 Администрация' in text or text == 'Администрация':
        if is_admin:
            from .admin_handlers import handle_admin_menu_text
            return handle_admin_menu_text(user_id, api)
        else:
            return api.send_message(user_id, "❌ У вас нет прав администратора.")
    
    # Обработка состояний
    current_state = user_states.get(user_id, 'main')
    
    if current_state == 'search':
        return handle_search_text(user_id, text, api)
    
    elif current_state == 'admin_send_notification_all':
        from .notification_handlers import handle_send_notification_all_text
        return handle_send_notification_all_text(user_id, text, api)
    
    elif current_state.startswith('admin_send_notification_role_'):
        from .notification_handlers import handle_send_notification_role_text
        return handle_send_notification_role_text(user_id, text, current_state, api)
    
    elif current_state == 'admin_schedule_input_date':
        from .shedule_handlers import handle_schedule_date_input
        return handle_schedule_date_input(user_id, text, api)
    
    elif current_state == 'admin_schedule_input_time':
        from .shedule_handlers import handle_schedule_time_input
        return handle_schedule_time_input(user_id, text, api)
    
    elif current_state == 'admin_schedule_input_details':
        from .shedule_handlers import handle_schedule_details_input
        return handle_schedule_details_input(user_id, text, api)
    
    # Для остальных сообщений - подсказка
    return api.send_message(
        user_id,
        """Используйте кнопки меню ниже или команды:
/start - Главное меню
/cancel - Отменить операцию"""
    )


def get_user_states():
    """Получить состояния пользователей"""
    return user_states


def get_user_data():
    """Получить данные пользователей"""
    return user_data


def set_user_state(user_id, state):
    """Установить состояние пользователя"""
    user_states[user_id] = state


def get_user_state(user_id):
    """Получить состояние пользователя"""
    return user_states.get(user_id, 'main')


def set_user_data(user_id, key, value):
    """Установить данные пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id][key] = value


def get_user_data_value(user_id, key, default=None):
    """Получить данные пользователя"""
    return user_data.get(user_id, {}).get(key, default)


def clear_user_data(user_id, key):
    """Очистить данные пользователя"""
    if user_id in user_data and key in user_data[user_id]:
        del user_data[user_id][key]