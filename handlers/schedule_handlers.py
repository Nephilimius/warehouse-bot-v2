#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
handlers/schedule_handlers.py
Хендлеры для работы с расписанием
"""

import logging
import re
from datetime import datetime, timedelta
from .utils import TelegramAPI, get_task_type_emoji
import database as db
from .keyboards import get_schedule_menu

logger = logging.getLogger(__name__)


def handle_schedule_menu_text(user_id, api: TelegramAPI):
    """Обработка меню расписания через текст"""
    return api.send_message(
        user_id,
        "🗓️ *Расписание*\n\nВыберите раздел для просмотра:",
        reply_markup=get_schedule_menu(),
        parse_mode='Markdown'
    )


def handle_schedule_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка меню расписания через callback"""
    return api.edit_message(
        user_id,
        message_id,
        "🗓️ *Расписание*\n\nВыберите раздел для просмотра:",
        reply_markup=get_schedule_menu(),
        parse_mode='Markdown'
    )


def handle_schedule_type(user_id, message_id, schedule_type, api: TelegramAPI):
    """Обработка выбора типа расписания"""
    schedule_items = db.get_schedule_by_type(schedule_type)
    type_emoji = get_task_type_emoji(schedule_type)
    
    if schedule_items:
        message = f"{type_emoji} *{schedule_type}* ({len(schedule_items)})\n\n"
        for i, item in enumerate(schedule_items[:10]):
            time_str = f"{item['start_time']}-{item['end_time']}"
            if time_str == "00:00-23:59": time_str = "Весь день"
            message += f"📅 {item['date']} ({time_str}) - @{item['username']}\n"
        if len(schedule_items) > 10:
            message += f"\n... и еще {len(schedule_items) - 10} записей."
    else:
        message = f"{type_emoji} *{schedule_type}*\n\n❌ Нет записей."
    
    return api.edit_message(
        user_id, message_id, message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К расписанию', 'callback_data': 'schedule'}]]},
        parse_mode='Markdown'
    )

# --- Утилиты для парсинга ---
def parse_date_input(date_text):
    date_text = date_text.strip().lower()
    if date_text in ['сегодня', 'today']: return datetime.now().date()
    if date_text in ['завтра', 'tomorrow']: return (datetime.now() + timedelta(days=1)).date()
    try: return datetime.strptime(date_text, '%d.%m.%Y').date()
    except: pass
    try: return datetime.strptime(f"{date_text}.{datetime.now().year}", '%d.%m.%Y').date()
    except: pass
    try: return datetime.strptime(date_text, '%Y-%m-%d').date()
    except: return None

def parse_time_input(time_text):
    time_text = time_text.strip().lower()
    if time_text in ['весь день', 'в течение дня']: return "00:00", "23:59"
    match = re.search(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', time_text)
    if match: return f"{match.group(1)}:{match.group(2)}", f"{match.group(3)}:{match.group(4)}"
    match = re.search(r'(\d{1,2})-(\d{1,2})', time_text)
    if match: return f"{match.group(1)}:00", f"{match.group(2)}:00"
    return None, None

# --- Обработчики текстового ввода в диалогах ---
def handle_text_message_schedule(user_id, text, state, data, api: TelegramAPI):
    if text.lower() == '/cancel':
        db.set_user_state(user_id, 'main', {})
        return api.send_message(user_id, "Действие отменено.")

    # Шаг: Ввод даты
    if state == 'admin_schedule_input_date':
        parsed_date = parse_date_input(text)
        if not parsed_date: return api.send_message(user_id, "❌ Неверный формат даты. Попробуйте еще раз.")
        
        data['creating_schedule']['date'] = parsed_date.strftime('%Y-%m-%d')
        db.set_user_state(user_id, 'admin_schedule_input_time', data)
        
        return api.send_message(user_id, "⏰ Теперь введите время (например, `9-12` или `весь день`):")

    # Шаг: Ввод времени
    elif state == 'admin_schedule_input_time':
        start_time, end_time = parse_time_input(text)
        if not start_time: return api.send_message(user_id, "❌ Неверный формат времени. Попробуйте еще раз.")

        data['creating_schedule']['start_time'] = start_time
        data['creating_schedule']['end_time'] = end_time
        
        task_type = data['creating_schedule']['type']
        if task_type in ['Уборка', 'Пересчеты']:
            db.set_user_state(user_id, 'admin_schedule_input_details', data)
            return api.send_message(user_id, "📝 Укажите детали (например, стеллажи) или напишите `пропустить`:")
        else:
            return _create_schedule_from_data(user_id, data, api)
    
    # Шаг: Ввод деталей
    elif state == 'admin_schedule_input_details':
        data['creating_schedule']['details'] = None if text.lower() == 'пропустить' else text
        return _create_schedule_from_data(user_id, data, api)

    return api.send_message(user_id, "Неизвестное действие.")


def _create_schedule_from_data(user_id, data, api: TelegramAPI):
    """Создание расписания из собранных данных (внутренняя функция)"""
    schedule_data = data['creating_schedule']
    success, result = db.create_schedule_task(
        user_id=schedule_data['assigned_to'],
        task_type=schedule_data['type'],
        date=schedule_data['date'],
        time_slot=f"{schedule_data['start_time']}-{schedule_data['end_time']}",
        shelves=schedule_data.get('details')
    )
    db.set_user_state(user_id, 'main', {}) # Сбрасываем состояние
    
    if success:
        message = f"✅ *Запись в расписание добавлена!*\n\n"
        message += f"Тип: {schedule_data['type']}\n"
        message += f"Исполнитель: @{schedule_data['assigned_username']}\n"
        message += f"Дата: {schedule_data['date']}"
    else:
        message = f"❌ *Ошибка!*\n\nНе удалось создать запись в расписании:\n`{result}`"
        
    return api.send_message(user_id, message, parse_mode='Markdown')


def handle_schedule_callback(user_id, message_id, query_id, callback_data, api: TelegramAPI):
    """Роутер для callback'ов расписания"""
    api.answer_callback_query(query_id)
    
    if callback_data == 'schedule_meals':
        return handle_schedule_type(user_id, message_id, 'Обеды', api)
    elif callback_data == 'schedule_cleaning':
        return handle_schedule_type(user_id, message_id, 'Уборка', api)
    elif callback_data == 'schedule_counting':
        return handle_schedule_type(user_id, message_id, 'Пересчеты', api)

    # Если мы здесь, значит это 'schedule' - главное меню раздела
    return handle_schedule_menu_callback(user_id, message_id, api)
