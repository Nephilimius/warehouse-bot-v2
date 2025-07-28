#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/callback_router.py
Главный роутер для обработки callback запросов
"""

import logging
from .utils import TelegramAPI
from .database_api import DatabaseAPI
from .keyboards import get_main_menu_keyboard
from .main_handlers import set_user_state

logger = logging.getLogger(__name__)


def handle_callback_query(user_id, callback_data, message_id, query_id, api: TelegramAPI):
    """Главный обработчик callback queries"""
    
    # Отвечаем на callback
    api.answer_callback_query(query_id)
    
    is_admin = DatabaseAPI.is_admin(user_id)
    
    try:
        logger.info(f"🔘 Обработка callback: {callback_data} от {user_id}")
        
        # Основные разделы
        if callback_data == 'search':
            set_user_state(user_id, 'search')
            return api.edit_message(
                user_id,
                message_id,
                "🔍 *Поиск и аналитика пользователя*\n\nВведите username для поиска:"
            )
        
        elif callback_data == 'profile':
            from .main_handlers import handle_profile_text
            # Для callback используем edit_message
            user = DatabaseAPI.get_or_create_user(user_id)
            
            if user:
                admin_status = "\n👑 *Статус:* Администратор" if is_admin else ""
                
                message = f"""👤 *Ваш профиль*

📱 *Username:* @{user.get('username', 'Не указан')}
🎭 *Роль:* {user.get('role', 'Не указана')}{admin_status}
📋 *Заданий выполнено:* {user.get('tasks_count', 0)}
⭐ *Средний рейтинг:* {user.get('average_rating', 0):.1f}
💎 *Качество работы:* {user.get('quality_score', 0):.1f}
🆔 *ID:* {user_id}"""
            else:
                message = f"👤 *Профиль*\n\n❌ Ошибка получения данных\n🆔 *ID:* {user_id}"
            
            return api.edit_message(
                user_id, message_id, message,
                reply_markup={'inline_keyboard': [[{'text': '◀️ Назад', 'callback_data': 'back_main'}]]},
                parse_mode='Markdown'
            )
        
        elif callback_data == 'back_main':
            set_user_state(user_id, 'main')
            return api.edit_message(
                user_id,
                message_id,
                "🏠 *Главное меню*\n\nИспользуйте кнопки внизу для навигации."
            )
        
        # Задания
        elif callback_data.startswith(('tasks', 'my_tasks', 'pending_tasks', 'completed_tasks', 'all_stats')):
            from .task_handlers import handle_task_callback
            return handle_task_callback(user_id, message_id, callback_data, api)
        
        # Расписание
        elif callback_data.startswith(('schedule', 'schedule_')):
            from .schedule_handlers import handle_schedule_callback
            return handle_schedule_callback(user_id, message_id, callback_data, api)
        
        # Отчеты
        elif callback_data.startswith(('reports', 'report_')):
            from .report_handlers import handle_report_callback
            return handle_report_callback(user_id, message_id, callback_data, api)
        
        # Уведомления
        elif callback_data.startswith(('notifications', 'my_notifications', 'notification_', 'send_', 'toggle_')):
            from .notification_handlers import handle_notification_callback
            return handle_notification_callback(user_id, message_id, callback_data, api)
        
        # Админские функции
        elif callback_data.startswith('admin') and is_admin:
            from .admin_handlers import handle_admin_callback
            return handle_admin_callback(user_id, message_id, callback_data, api)
        
        elif callback_data.startswith('admin') and not is_admin:
            return api.edit_message(
                user_id,
                message_id,
                "❌ У вас нет прав администратора"
            )
        
        # Функции удаления расписания (для админов)
        elif callback_data.startswith(('delete_item_', 'confirm_delete_', 'cancel_delete_')) and is_admin:
            from .admin_handlers import handle_admin_callback
            return handle_admin_callback(user_id, message_id, callback_data, api)
        
        elif callback_data.startswith(('delete_item_', 'confirm_delete_', 'cancel_delete_')) and not is_admin:
            return api.edit_message(
                user_id, message_id,
                "❌ У вас нет прав администратора"
            )
        
        # По умолчанию
        else:
            logger.warning(f"⚠️  Неизвестная callback_data: {callback_data}")
            return api.edit_message(
                user_id,
                message_id,
                f"❓ Функция `{callback_data}` в разработке",
                reply_markup={'inline_keyboard': [[{'text': '◀️ Назад', 'callback_data': 'back_main'}]]}
            )
        
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_callback_query: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback в главное меню
        return api.edit_message(
            user_id,
            message_id,
            "❌ Произошла ошибка, возвращаю в главное меню",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
