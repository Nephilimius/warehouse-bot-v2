#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/notification_handlers.py
Хендлеры для работы с уведомлениями
"""

import logging
from .utils import TelegramAPI
from .database_api import db
from .keyboards import get_notifications_menu, get_back_button
from .main_handlers import set_user_state, get_user_states

logger = logging.getLogger(__name__)


def handle_notifications_menu_text(user_id, api: TelegramAPI):
    """Обработка меню уведомлений через текст"""
    
    is_admin = db.is_admin(user_id)
    
    # Получаем настройки пользователя
    settings = db.get_notification_settings(user_id)
    
    # Получаем количество непрочитанных уведомлений
    notifications = db.get_user_notifications(user_id, 50)
    unread_count = len([n for n in notifications if not n.get('is_read', True)])
    
    message = f"""🔔 *Уведомления*

📊 *Ваша статистика:*
• Всего уведомлений: {len(notifications)}
• Непрочитанных: {unread_count}

⚙️ *Настройки:*"""
    
    if settings:
        status_emoji = lambda x: "✅" if x else "❌"
        message += f"""
• Общие уведомления: {status_emoji(settings.get('general_notifications', True))}
• Напоминания о задачах: {status_emoji(settings.get('task_reminders', True))}
• Обновления расписания: {status_emoji(settings.get('schedule_updates', True))}
• Уведомления о рейтинге: {status_emoji(settings.get('rating_notifications', True))}"""
    else:
        message += "\n❌ Ошибка загрузки настроек"
    
    message += "\n\nВыберите действие:"
    
    return api.send_message(
        user_id,
        message,
        reply_markup=get_notifications_menu(is_admin),
        parse_mode='Markdown'
    )


def handle_notifications_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка меню уведомлений через callback"""
    
    is_admin = db.is_admin(user_id)
    
    # Получаем настройки пользователя
    settings = db.get_notification_settings(user_id)
    
    # Получаем количество непрочитанных уведомлений
    notifications = db.get_user_notifications(user_id, 50)
    unread_count = len([n for n in notifications if not n.get('is_read', True)])
    
    message = f"""🔔 *Уведомления*

📊 *Ваша статистика:*
• Всего уведомлений: {len(notifications)}
• Непрочитанных: {unread_count}

⚙️ *Настройки:*"""
    
    if settings:
        status_emoji = lambda x: "✅" if x else "❌"
        message += f"""
• Общие уведомления: {status_emoji(settings.get('general_notifications', True))}
• Напоминания о задачах: {status_emoji(settings.get('task_reminders', True))}
• Обновления расписания: {status_emoji(settings.get('schedule_updates', True))}
• Уведомления о рейтинге: {status_emoji(settings.get('rating_notifications', True))}"""
    else:
        message += "\n❌ Ошибка загрузки настроек"
    
    message += "\n\nВыберите действие:"
    
    return api.edit_message(
        user_id,
        message_id,
        message,
        reply_markup=get_notifications_menu(is_admin),
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
            
            # Обрезаем длинное сообщение
            text = notif.get('message', '')
            if len(text) > 60:
                text = text[:60] + "..."
            message += f"💬 {text}\n\n"
            
            if i >= 9:  # Показываем максимум 10
                break
    else:
        message = "📱 *Ваши уведомления*\n\n❌ У вас пока нет уведомлений"
    
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
            [{'text': f"{'✅' if settings.get('general_notifications', True) else '❌'} Общие уведомления", 
              'callback_data': 'toggle_general_notifications'}],
            [{'text': f"{'✅' if settings.get('task_reminders', True) else '❌'} Напоминания о задачах", 
              'callback_data': 'toggle_task_reminders'}],
            [{'text': f"{'✅' if settings.get('schedule_updates', True) else '❌'} Обновления расписания", 
              'callback_data': 'toggle_schedule_updates'}],
            [{'text': f"{'✅' if settings.get('rating_notifications', True) else '❌'} Уведомления о рейтинге", 
              'callback_data': 'toggle_rating_notifications'}],
            [{'text': '◀️ К уведомлениям', 'callback_data': 'notifications'}]
        ]
        
        message = "⚙️ *Настройки уведомлений*\n\nНажмите на настройку для изменения:"
    else:
        keyboard = [[{'text': '◀️ К уведомлениям', 'callback_data': 'notifications'}]]
        message = "⚙️ *Настройки уведомлений*\n\n❌ Ошибка загрузки настроек"
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': keyboard},
        parse_mode='Markdown'
    )


def handle_send_notification_all_text(user_id, text, api: TelegramAPI):
    """Обработка отправки уведомления всем пользователям"""
    
    if text.strip():
        sent_count = db.send_notification_to_all_users("📢 Общее уведомление", text.strip())
        set_user_state(user_id, 'main')
        
        from .keyboards import get_reply_keyboard
        
        return api.send_message(
            user_id,
            f"✅ *Уведомление отправлено!*\n\n📊 Получателей: {sent_count}\n💬 Сообщение: {text[:100]}{'...' if len(text) > 100 else ''}",
            reply_markup=get_reply_keyboard(db.is_admin(user_id)),
            parse_mode='Markdown'
        )
    else:
        return api.send_message(user_id, "❌ Сообщение не может быть пустым")


def handle_send_notification_role_text(user_id, text, current_state, api: TelegramAPI):
    """Обработка отправки уведомления по роли"""
    
    role = current_state.replace('admin_send_notification_role_', '')
    
    if text.strip():
        sent_count = db.send_notification_to_all_users(f"🎯 Уведомление для {role}", text.strip(), role)
        set_user_state(user_id, 'main')
        
        from .utils import get_role_emoji
        from .keyboards import get_reply_keyboard
        
        role_emoji = get_role_emoji(role)
        
        return api.send_message(
            user_id,
            f"✅ *Уведомление отправлено!*\n\n🎯 Роль: {role_emoji} {role}\n📊 Получателей: {sent_count}\n💬 Сообщение: {text[:100]}{'...' if len(text) > 100 else ''}",
            reply_markup=get_reply_keyboard(db.is_admin(user_id)),
            parse_mode='Markdown'
        )
    else:
        return api.send_message(user_id, "❌ Сообщение не может быть пустым")


def handle_notification_callback(user_id, message_id, callback_data, api: TelegramAPI):
    """Роутер для callback'ов уведомлений"""
    
    if callback_data == 'notifications':
        return handle_notifications_menu_callback(user_id, message_id, api)
    
    elif callback_data == 'my_notifications':
        return handle_my_notifications(user_id, message_id, api)
    
    elif callback_data == 'notification_settings':
        return handle_notification_settings(user_id, message_id, api)
    
    elif callback_data == 'send_notification_all':
        if not db.is_admin(user_id):
            return api.edit_message(user_id, message_id, "❌ У вас нет прав администратора")
        
        set_user_state(user_id, 'admin_send_notification_all')
        return api.edit_message(
            user_id, message_id,
            "📢 *Отправка уведомления всем пользователям*\n\nВведите сообщение для отправки:\n\n_Или /cancel для отмены_",
            parse_mode='Markdown'
        )
    
    elif callback_data == 'send_notification_role':
        if not db.is_admin(user_id):
            return api.edit_message(user_id, message_id, "❌ У вас нет прав администратора")
        
        keyboard = [
            [{'text': '👑 Только ДС', 'callback_data': 'send_to_role_ДС'}],
            [{'text': '🎖️ Только ЗДС', 'callback_data': 'send_to_role_ЗДС'}],
            [{'text': '👷 Только Кладовщики', 'callback_data': 'send_to_role_Кладовщик'}],
            [{'text': '◀️ К уведомлениям', 'callback_data': 'notifications'}]
        ]
        
        return api.edit_message(
            user_id, message_id,
            "🎯 *Отправка по роли*\n\nВыберите роль:",
            reply_markup={'inline_keyboard': keyboard},
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith('send_to_role_'):
        if not db.is_admin(user_id):
            return api.edit_message(user_id, message_id, "❌ У вас нет прав администратора")
        
        role = callback_data.replace('send_to_role_', '')
        set_user_state(user_id, f'admin_send_notification_role_{role}')
        
        from .utils import get_role_emoji
        role_emoji = get_role_emoji(role)
        
        return api.edit_message(
            user_id, message_id,
            f"🎯 *Отправка уведомления: {role_emoji} {role}*\n\nВведите сообщение для отправки:\n\n_Или /cancel для отмены_",
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith('toggle_'):
        setting_name = callback_data.replace('toggle_', '')
        settings = db.get_notification_settings(user_id)
        
        if settings:
            # Переключаем настройку
            new_value = not settings.get(setting_name, True)
            settings[setting_name] = new_value
            
            # Сохраняем
            success = db.update_notification_settings(user_id, settings)
            
            if success:
                # Обновляем меню настроек
                return handle_notification_settings(user_id, message_id, api)
            else:
                return api.edit_message(
                    user_id, message_id,
                    "❌ Ошибка обновления настроек",
                    reply_markup={'inline_keyboard': [[{'text': '◀️ К уведомлениям', 'callback_data': 'notifications'}]]}
                )
        else:
            return api.edit_message(
                user_id, message_id,
                "❌ Ошибка загрузки настроек",
                reply_markup={'inline_keyboard': [[{'text': '◀️ К уведомлениям', 'callback_data': 'notifications'}]]}
            )
    
    else:
        return api.edit_message(
            user_id,
            message_id,
            f"❓ Функция `{callback_data}` в разработке",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К уведомлениям', 'callback_data': 'notifications'}]]}
        )
