#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/main_handlers.py
Основные хендлеры команд и текстовых сообщений
"""

import logging
import database as db
from .utils import TelegramAPI
from .keyboards import get_main_menu_keyboard, get_reply_keyboard, get_back_button

logger = logging.getLogger(__name__)

# Глобальные состояния пользователей
user_states = {}
user_data = {}


def handle_start_command(user_id, username, first_name, api: TelegramAPI):
    """Обработка команды /start"""
    
    user_states[user_id] = 'main'
    
    # Получаем пользователя из базы
    user = db.get_or_create_user(user_id, username)
    role = user.get('role', 'Кладовщик') if user else 'Кладовщик'
    is_admin = db.is_admin(user_id)
    
    admin_text = '👑 У вас есть права администратора!' if is_admin else ''
    
    welcome_text = f"""🤖 *Добро пожаловать, {first_name}!*

*Ваша роль:* {role}
{admin_text}

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
    is_admin = db.is_admin(user_id)
    
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
    
    # Убираем @ если есть
    username = text.replace("@", "")
    
    # Поиск пользователя (пока заглушка)
    users = db.get_all_users()
    found_user = None
    
    for user in users:
        logger.info(f"Поиск: ищу '{username}'")
        user_username = user.get('username', '')
        logger.info(f"Проверяю: '{user_username}' vs '{username}'")
        
        if user_username.lower() == username.lower():
            found_user = user
            logger.info(f"Найден пользователь: {found_user}")
            break
    
    if found_user:
        from .utils import get_role_emoji
        
        role_emoji = get_role_emoji(found_user['role'])
        
        username_display = found_user['username']
        role_display = found_user['role']
        tasks_count = found_user.get('tasks_count', 0)
        avg_rating = found_user.get('average_rating', 0)
        telegram_id = found_user['telegram_id']
        
        message = f"""🔍 *Результат поиска*

👤 *@{username_display}*
{role_emoji} Роль: {found_user['role']}
📋 Всего задач: {tasks_count}
⭐ Средний рейтинг: {avg_rating:.1f}
🆔 ID: {telegram_id}"""
    else:
        message = (f"🔍 *Результат поиска*\n\n"
                  f"❌ Пользователь `@{username}` не найден")
    
    is_admin = db.is_admin(user_id)
    return api.send_message(
        user_id,
        message,
        reply_markup=get_main_menu_keyboard(is_admin)
    )


def handle_profile_text(user_id, api: TelegramAPI):
    """Обработка профиля через текст"""
    
    # Получаем данные пользователя из базы
    user = db.get_or_create_user(user_id)
    
    if user:
        is_admin = db.is_admin(user_id)
        admin_status = "\n👑 *Статус:* Администратор" if is_admin else ""
        
        username_display = user.get('username', 'Не указан')
        role_display = user.get('role', 'Не указана')
        tasks_count = user.get('tasks_count', 0)
        avg_rating = user.get('average_rating', 0)
        quality_score = user.get('quality_score', 0)
        
        message = f"""👤 *Ваш профиль*

📱 *Username:* @{username_display}
🎭 *Роль:* {role_display}{admin_status}
📋 *Заданий выполнено:* {tasks_count}
⭐ *Средний рейтинг:* {avg_rating:.1f}
💎 *Качество работы:* {quality_score:.1f}
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
    
    is_admin = db.is_admin(user_id)
    
    # Команды
    if text == "/start":
        first_name = "Пользователь"  # Можно получить из update
        return handle_start_command(user_id, username, first_name, api)
    
    elif text == "/cancel":
        return handle_cancel_command(user_id, api)
    
    # Обработка кнопок меню
    elif '🔍 Найти' in text or text == 'Найти':
        user_states[user_id] = 'search'
        return api.send_message(
            user_id,
            ("🔍 *Поиск и аналитика пользователя*\n\n"
             "Введите username для поиска:"),
            parse_mode='Markdown'
        )
    
    elif '📄 Задания' in text or text == 'Задания':
        from .task_handlers import handle_tasks_menu_text
        return handle_tasks_menu_text(user_id, api)
    
    elif '🗓️ Расписание' in text or text == 'Расписание':
        from .schedule_handlers import handle_schedule_menu_text
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
        from .schedule_handlers import handle_schedule_date_input
        return handle_schedule_date_input(user_id, text, api)
    
    elif current_state == 'admin_schedule_input_time':
        from .schedule_handlers import handle_schedule_time_input
        return handle_schedule_time_input(user_id, text, api)
    
    elif current_state == 'admin_schedule_input_details':
        from .schedule_handlers import handle_schedule_details_input
        return handle_schedule_details_input(user_id, text, api)
    
    # Для остальных сообщений - подсказка
    return api.send_message(
        user_id,
        ("Используйте кнопки меню ниже или команды:\n"
         "/start - Главное меню\n"
         "/cancel - Отменить операцию")
    )