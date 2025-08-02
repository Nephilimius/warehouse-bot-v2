#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/callback_router.py
Главный роутер для обработки callback requests - ОТЛАДОЧНАЯ ВЕРСИЯ
"""

import logging

logger = logging.getLogger(__name__)


def handle_callback_query(user_id, callback_data, message_id, query_id, api):
    """Главный обработчик callback queries - ОТЛАДОЧНАЯ ВЕРСИЯ"""
    
    logger.info(f"🔘 ВХОД В handle_callback_query: user={user_id}, data='{callback_data}', msg_id={message_id}")
    
    # НЕ отвечаем на callback здесь - это делается в bot_modular.py
    
    from config import ADMINS
    is_admin = user_id in ADMINS
    
    logger.info(f"🔘 Пользователь {user_id} {'АДМИН' if is_admin else 'НЕ АДМИН'}")
    
    try:
        # Основные разделы
        if callback_data == 'search':
            logger.info("🔍 Обработка callback: search")
            try:
                from .main_handlers import set_user_state
                set_user_state(user_id, 'search')
                success, result = api.edit_message(
                    user_id,
                    message_id,
                    "🔍 *Поиск и аналитика пользователя*\n\nВведите username для поиска:",
                    parse_mode='Markdown'
                )
                logger.info(f"🔍 Результат edit_message: success={success}")
                return success, result
            except Exception as e:
                logger.error(f"❌ Ошибка в search callback: {e}")
                return False, str(e)
        
        elif callback_data == 'profile':
            logger.info("👤 Обработка callback: profile")
            try:
                from .main_handlers import get_or_create_user_sync
                # Для callback используем edit_message
                user = get_or_create_user_sync(user_id)
                
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
                
                success, result = api.edit_message(
                    user_id, message_id, message,
                    reply_markup={'inline_keyboard': [[{'text': '◀️ Назад', 'callback_data': 'back_main'}]]},
                    parse_mode='Markdown'
                )
                logger.info(f"👤 Результат edit_message: success={success}")
                return success, result
            except Exception as e:
                logger.error(f"❌ Ошибка в profile callback: {e}")
                return False, str(e)
        
        elif callback_data == 'back_main':
            logger.info("🏠 Обработка callback: back_main")
            try:
                from .main_handlers import set_user_state, get_main_menu_keyboard
                set_user_state(user_id, 'main')
                success, result = api.edit_message(
                    user_id,
                    message_id,
                    "🏠 *Главное меню*\n\nИспользуйте кнопки внизу для навигации.",
                    reply_markup=get_main_menu_keyboard(is_admin),
                    parse_mode='Markdown'
                )
                logger.info(f"🏠 Результат edit_message: success={success}")
                return success, result
            except Exception as e:
                logger.error(f"❌ Ошибка в back_main callback: {e}")
                return False, str(e)
        
        # Задания
        elif callback_data == 'tasks':
            logger.info("📄 Обработка callback: tasks")
            try:
                from .main_handlers import get_tasks_menu
                success, result = api.edit_message(
                    user_id,
                    message_id,
                    "📄 *Управление заданиями*\n\nВыберите действие:",
                    reply_markup=get_tasks_menu(is_admin),
                    parse_mode='Markdown'
                )
                logger.info(f"📄 Результат edit_message: success={success}")
                return success, result
            except Exception as e:
                logger.error(f"❌ Ошибка в tasks callback: {e}")
                return False, str(e)
        
        elif callback_data == 'my_tasks':
            logger.info("📝 Обработка callback: my_tasks")
            return handle_my_tasks_callback(user_id, message_id, api)
        
        elif callback_data == 'pending_tasks':
            logger.info("⏳ Обработка callback: pending_tasks")
            return handle_pending_tasks_callback(user_id, message_id, api, is_admin)
        
        elif callback_data == 'completed_tasks':
            logger.info("✅ Обработка callback: completed_tasks")
            return handle_completed_tasks_callback(user_id, message_id, api, is_admin)
        
        # Расписание
        elif callback_data == 'schedule':
            logger.info("🗓️ Обработка callback: schedule")
            try:
                from .main_handlers import get_schedule_menu
                success, result = api.edit_message(
                    user_id,
                    message_id,
                    "🗓️ *Расписание*\n\nВыберите раздел для просмотра:",
                    reply_markup=get_schedule_menu(),
                    parse_mode='Markdown'
                )
                logger.info(f"🗓️ Результат edit_message: success={success}")
                return success, result
            except Exception as e:
                logger.error(f"❌ Ошибка в schedule callback: {e}")
                return False, str(e)
        
        elif callback_data in ['schedule_meals', 'schedule_cleaning', 'schedule_counting']:
            logger.info(f"🗓️ Обработка callback расписания: {callback_data}")
            return handle_schedule_type_callback(user_id, message_id, callback_data, api)
        
        # Отчеты
        elif callback_data == 'reports':
            logger.info("📊 Обработка callback: reports")
            try:
                from .main_handlers import get_reports_menu
                success, result = api.edit_message(
                    user_id,
                    message_id,
                    "📊 *Отчеты и аналитика*\n\nВыберите тип отчета:",
                    reply_markup=get_reports_menu(),
                    parse_mode='Markdown'
                )
                logger.info(f"📊 Результат edit_message: success={success}")
                return success, result
            except Exception as e:
                logger.error(f"❌ Ошибка в reports callback: {e}")
                return False, str(e)
        
        # Уведомления
        elif callback_data == 'notifications':
            logger.info("🔔 Обработка callback: notifications")
            try:
                from .main_handlers import get_notifications_menu
                success, result = api.edit_message(
                    user_id,
                    message_id,
                    "🔔 *Уведомления*\n\nВыберите действие:",
                    reply_markup=get_notifications_menu(is_admin),
                    parse_mode='Markdown'
                )
                logger.info(f"🔔 Результат edit_message: success={success}")
                return success, result
            except Exception as e:
                logger.error(f"❌ Ошибка в notifications callback: {e}")
                return False, str(e)
        
        # Админские функции
        elif callback_data == 'admin' and is_admin:
            logger.info("👑 Обработка callback: admin")
            try:
                from .main_handlers import get_admin_menu
                success, result = api.edit_message(
                    user_id,
                    message_id,
                    "👑 *Панель администратора*\n\nВыберите действие:",
                    reply_markup=get_admin_menu(),
                    parse_mode='Markdown'
                )
                logger.info(f"👑 Результат edit_message: success={success}")
                return success, result
            except Exception as e:
                logger.error(f"❌ Ошибка в admin callback: {e}")
                return False, str(e)
        
        elif callback_data.startswith('admin') and not is_admin:
            logger.warning(f"🚫 Неавторизованная попытка доступа к админке от {user_id}")
            success, result = api.edit_message(
                user_id,
                message_id,
                "❌ У вас нет прав администратора"
            )
            return success, result
        
        # По умолчанию
        else:
            logger.warning(f"❓ Неизвестная callback_data: '{callback_data}'")
            success, result = api.edit_message(
                user_id,
                message_id,
                f"❓ Функция `{callback_data}` в разработке",
                reply_markup={'inline_keyboard': [[{'text': '◀️ Назад', 'callback_data': 'back_main'}]]}
            )
            return success, result
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ошибка в handle_callback_query: {e}")
        import traceback
        traceback.print_exc()
        
        # В случае ошибки возвращаем простое сообщение
        try:
            success, result = api.edit_message(
                user_id,
                message_id,
                "❌ Произошла ошибка, попробуйте еще раз",
                reply_markup={'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'back_main'}]]}
            )
            return success, result
        except:
            return False, "Critical error in callback handler"


def handle_my_tasks_callback(user_id, message_id, api):
    """Обработка просмотра моих задач"""
    logger.info(f"📝 handle_my_tasks_callback для {user_id}")
    
    try:
        # Заглушка - просто возвращаем сообщение
        success, result = api.edit_message(
            user_id,
            message_id,
            "📝 *Ваши задания*\n\n❌ Функция в разработке\n\n_Подключение к базе данных..._",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]},
            parse_mode='Markdown'
        )
        logger.info(f"📝 Результат: success={success}")
        return success, result
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_my_tasks_callback: {e}")
        return False, str(e)


def handle_pending_tasks_callback(user_id, message_id, api, is_admin):
    """Обработка просмотра ожидающих задач"""
    logger.info(f"⏳ handle_pending_tasks_callback для {user_id}, админ: {is_admin}")
    
    try:
        title = "⏳ *Все ожидающие задания*" if is_admin else "⏳ *Ваши ожидающие задания*"
        success, result = api.edit_message(
            user_id,
            message_id,
            f"{title}\n\n❌ Функция в разработке\n\n_Подключение к базе данных..._",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]},
            parse_mode='Markdown'
        )
        logger.info(f"⏳ Результат: success={success}")
        return success, result
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_pending_tasks_callback: {e}")
        return False, str(e)


def handle_completed_tasks_callback(user_id, message_id, api, is_admin):
    """Обработка просмотра выполненных задач"""
    logger.info(f"✅ handle_completed_tasks_callback для {user_id}, админ: {is_admin}")
    
    try:
        title = "✅ *Все выполненные задания*" if is_admin else "✅ *Ваши выполненные задания*"
        success, result = api.edit_message(
            user_id,
            message_id,
            f"{title}\n\n❌ Функция в разработке\n\n_Подключение к базе данных..._",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К заданиям', 'callback_data': 'tasks'}]]},
            parse_mode='Markdown'
        )
        logger.info(f"✅ Результат: success={success}")
        return success, result
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_completed_tasks_callback: {e}")
        return False, str(e)


def handle_schedule_type_callback(user_id, message_id, callback_data, api):
    """Обработка выбора типа расписания"""
    logger.info(f"🗓️ handle_schedule_type_callback: {callback_data}")
    
    type_mapping = {
        'schedule_meals': 'Обеды',
        'schedule_cleaning': 'Уборка', 
        'schedule_counting': 'Пересчеты'
    }
    
    schedule_type = type_mapping.get(callback_data, 'Неизвестно')
    type_emoji = get_task_type_emoji(schedule_type)
    
    try:
        success, result = api.edit_message(
            user_id,
            message_id,
            f"{type_emoji} *{schedule_type}*\n\n❌ Функция в разработке\n\n_Подключение к базе данных..._",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К расписанию', 'callback_data': 'schedule'}]]},
            parse_mode='Markdown'
        )
        logger.info(f"🗓️ Результат: success={success}")
        return success, result
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_schedule_type_callback: {e}")
        return False, str(e)


def get_task_type_emoji(task_type):
    """Возвращает эмодзи для типа задачи"""
    return {
        "Обеды": "🍽️",
        "Уборка": "🧹", 
        "Пересчеты": "🔢"
    }.get(task_type, "📋")