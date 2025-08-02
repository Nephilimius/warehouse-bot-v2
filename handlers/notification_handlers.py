#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/notification_handlers.py
Хендлеры для работы с уведомлениями
"""

import logging
from .utils import TelegramAPI, is_admin, get_role_emoji
import database as db
from .keyboards import get_notifications_menu

logger = logging.getLogger(__name__)


def handle_notifications_menu_text(user_id, api: TelegramAPI):
    """Обработка меню уведомлений через текст"""
    is_admin_user = is_admin(user_id)
    return api.send_message(
        user_id,
        "🔔 *Уведомления*\n\nВыберите действие:",
        reply_markup=get_notifications_menu(is_admin_user),
        parse_mode='Markdown'
    )


def handle_notifications_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка меню уведомлений через callback"""
    is_admin_user = is_admin(user_id)
    return api.edit_message(
        user_id,
        message_id,
        "🔔 *Уведомления*\n\nВыберите действие:",
        reply_markup=get_notifications_menu(is_admin_user),
        parse_mode='Markdown'
    )


def handle_my_notifications(user_id, message_id, api: TelegramAPI):
    """Обработка просмотра уведомлений пользователя"""
    notifications = db.get_user_notifications(user_id, 10)
    
    if notifications:
        message = "📱 *Ваши уведомления* (последние 10)\n\n"
        for i, notif in enumerate(notifications):
            status = "🔹" if notif.get('is_read', True) else "🔸"
            date = notif.get('created_at', '')[:16] if notif.get('created_at') else ''
            message += f"{status} *{notif.get('title', 'Без названия')}*\n"
            message += f"📅 {date}\n"
            text = notif.get('message', '')
            if len(text) > 60: text = text[:60] + "..."
            message += f"💬 {text}\n\n"
    else:
        message = "📱 *Ваши уведомления*\n\n❌ У вас пока нет уведомлений."
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К уведомлениям', 'callback_data': 'notifications'}]]},
        parse_mode='Markdown'
    )


def handle_notification_settings(user_id, message_id, api: TelegramAPI):
    """Обработка настроек уведомлений"""
    settings = db.get_notification_settings(user_id)
    
    if settings:
        keyboard = [
            [{'text': f"{'✅' if settings.get('general_notifications', True) else '❌'} Общие", 'callback_data': 'notifications_toggle_general'}],
            [{'text': f"{'✅' if settings.get('task_reminders', True) else '❌'} О задачах", 'callback_data': 'notifications_toggle_task'}],
            [{'text': f"{'✅' if settings.get('schedule_updates', True) else '❌'} О расписании", 'callback_data': 'notifications_toggle_schedule'}],
            [{'text': f"{'✅' if settings.get('rating_notifications', True) else '❌'} О рейтинге", 'callback_data': 'notifications_toggle_rating'}],
            [{'text': '◀️ К уведомлениям', 'callback_data': 'notifications'}]
        ]
        message = "⚙️ *Настройки уведомлений*\n\nНажмите на настройку для изменения:"
    else:
        keyboard = [[{'text': '◀️ К уведомлениям', 'callback_data': 'notifications'}]]
        message = "⚙️ *Настройки уведомлений*\n\n❌ Ошибка загрузки настроек."
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': keyboard},
        parse_mode='Markdown'
    )


def handle_text_message_notification(user_id, text, state, data, api: TelegramAPI):
    """Обработка ввода текста для отправки уведомлений"""
    if text.lower() == '/cancel':
        db.set_user_state(user_id, 'main', {})
        return api.send_message(user_id, "Отправка отменена.")

    # Отправка всем
    if state == 'notifications_send_all':
        # Здесь должна быть логика отправки всем
        db.set_user_state(user_id, 'main', {})
        return api.send_message(user_id, f"✅ Уведомление отправлено всем!\n\n_{text}_", parse_mode='Markdown')
        
    # Отправка по роли
    elif state.startswith('notifications_send_role_'):
        role = state.replace('notifications_send_role_', '')
        # Здесь должна быть логика отправки по роли
        db.set_user_state(user_id, 'main', {})
        return api.send_message(user_id, f"✅ Уведомление отправлено роли *{role}*!\n\n_{text}_", parse_mode='Markdown')
    
    return api.send_message(user_id, "Неизвестное действие.")


def handle_notification_callback(user_id, message_id, query_id, callback_data, api: TelegramAPI):
    """Роутер для callback'ов уведомлений"""
    api.answer_callback_query(query_id) # Отвечаем на callback

    if callback_data == 'notifications_my':
        return handle_my_notifications(user_id, message_id, api)
    
    elif callback_data == 'notifications_settings':
        return handle_notification_settings(user_id, message_id, api)
    
    elif callback_data == 'notifications_send_all':
        if not is_admin(user_id): return api.edit_message(user_id, message_id, "❌ Нет прав")
        db.set_user_state(user_id, 'notifications_send_all', {})
        return api.edit_message(user_id, message_id, "📢 Введите сообщение для *всех* пользователей:", parse_mode='Markdown')

    elif callback_data == 'notifications_send_role':
        if not is_admin(user_id): return api.edit_message(user_id, message_id, "❌ Нет прав")
        keyboard = [
            [{'text': f'{get_role_emoji("ДС")} ДС', 'callback_data': 'notifications_select_role_ДС'}],
            [{'text': f'{get_role_emoji("ЗДС")} ЗДС', 'callback_data': 'notifications_select_role_ЗДС'}],
            [{'text': f'{get_role_emoji("Кладовщик")} Кладовщики', 'callback_data': 'notifications_select_role_Кладовщик'}],
            [{'text': '◀️ Назад', 'callback_data': 'notifications'}]
        ]
        return api.edit_message(user_id, message_id, "🎯 Выберите роль для отправки:", reply_markup={'inline_keyboard': keyboard})

    elif callback_data.startswith('notifications_select_role_'):
        role = callback_data.replace('notifications_select_role_', '')
        db.set_user_state(user_id, f'notifications_send_role_{role}')
        return api.edit_message(user_id, message_id, f"🎯 Введите сообщение для роли *{role}*:", parse_mode='Markdown')

    elif callback_data.startswith('notifications_toggle_'):
        setting_name = callback_data.replace('notifications_toggle_', '')
        # Здесь должна быть логика переключения настроек
        return handle_notification_settings(user_id, message_id, api) # Просто обновляем меню

    # Если мы здесь, значит это 'notifications' - главное меню раздела
    return handle_notifications_menu_callback(user_id, message_id, api)
