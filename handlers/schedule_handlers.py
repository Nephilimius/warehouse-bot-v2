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
from .database_api import db
from .keyboards import get_schedule_menu, get_back_button
from .main_handlers import (
    get_user_states, get_user_data, set_user_state, 
    set_user_data, get_user_data_value, clear_user_data
)

logger = logging.getLogger(__name__)


def handle_schedule_menu_text(user_id, api: TelegramAPI):
    """Обработка меню расписания через текст"""
    
    # Получаем статистику
    stats = {}
    for schedule_type in ['Обеды', 'Уборка', 'Пересчеты']:
        items = db.get_schedule_by_type(schedule_type)
        stats[schedule_type] = len(items) if items else 0
    
    total = sum(stats.values())
    
    if total > 0:
        details = []
        for stype, count in stats.items():
            if count > 0:
                details.append(f"{count} - {stype.lower()}")
        
        stats_text = f"📊 В расписании записей: *{total}*, из них {', '.join(details)}"
    else:
        stats_text = "📋 В расписании пока нет записей"
    
    return api.send_message(
        user_id,
        f"""🗓️ *Расписание*

{stats_text}

Выберите раздел для просмотра:""",
        reply_markup=get_schedule_menu(),
        parse_mode='Markdown'
    )


def handle_schedule_menu_callback(user_id, message_id, api: TelegramAPI):
    """Обработка меню расписания через callback"""
    
    # Получаем статистику
    stats = {}
    for schedule_type in ['Обеды', 'Уборка', 'Пересчеты']:
        items = db.get_schedule_by_type(schedule_type)
        stats[schedule_type] = len(items) if items else 0
    
    total = sum(stats.values())
    
    if total > 0:
        details = []
        for stype, count in stats.items():
            if count > 0:
                details.append(f"{count} - {stype.lower()}")
        
        stats_text = f"📊 В расписании записей: *{total}*, из них {', '.join(details)}"
    else:
        stats_text = "📋 В расписании пока нет записей"
    
    return api.edit_message(
        user_id,
        message_id,
        f"🗓️ *Расписание*\n\n{stats_text}\n\nВыберите раздел для просмотра:",
        reply_markup=get_schedule_menu()
    )


def handle_schedule_type(user_id, message_id, callback_data, api: TelegramAPI):
    """Обработка выбора типа расписания"""
    
    type_mapping = {
        'schedule_meals': 'Обеды',
        'schedule_cleaning': 'Уборка', 
        'schedule_counting': 'Пересчеты'
    }
    
    schedule_type = type_mapping.get(callback_data)
    if not schedule_type:
        return api.edit_message(
            user_id,
            message_id,
            "❌ Неизвестный тип расписания"
        )
    
    # Получаем реальные данные
    schedule_items = db.get_schedule_by_type(schedule_type)
    
    # Формируем сообщение
    type_emoji = get_task_type_emoji(schedule_type)
    
    if schedule_items:
        message = f"{type_emoji} *{schedule_type}*\n\n"
        
        for i, item in enumerate(schedule_items[:10]):
            time_str = f"{item['start_time']}-{item['end_time']}"
            if time_str == "00:00-23:59":
                time_str = "Весь день"
            
            message += f"📅 {item['date']}\n"
            message += f"⏰ {time_str}\n"
            message += f"👤 @{item['username']}\n\n"
        
        if len(schedule_items) > 10:
            message += f"... и еще {len(schedule_items) - 10} записей"
    else:
        message = f"{type_emoji} *{schedule_type}*\n\n❌ Нет записей"
    
    return api.edit_message(
        user_id,
        message_id,
        message,
        reply_markup={'inline_keyboard': [[{'text': '◀️ К расписанию', 'callback_data': 'schedule'}]]},
        parse_mode='Markdown'
    )


def parse_date_input(date_text):
    """Парсит дату из текстового ввода"""
    
    date_text = date_text.strip().lower()
    
    if date_text in ['сегодня', 'today']:
        return datetime.now().date()
    elif date_text in ['завтра', 'tomorrow']:
        return (datetime.now() + timedelta(days=1)).date()
    
    # Форматы дат
    formats = [
        (r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '%d.%m.%Y'),
        (r'(\d{1,2})\.(\d{1,2})', f'%d.%m.{datetime.now().year}'),
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),
        (r'(\d{1,2})/(\d{1,2})', f'%d/%m/{datetime.now().year}'),
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
    ]
    
    for pattern, fmt in formats:
        match = re.match(pattern, date_text)
        if match:
            try:
                if '%Y' not in fmt:
                    parsed_date = datetime.strptime(date_text + f'.{datetime.now().year}', fmt.replace(f'.{datetime.now().year}', '.%Y')).date()
                else:
                    parsed_date = datetime.strptime(date_text, fmt).date()
                
                if parsed_date >= datetime.now().date():
                    return parsed_date
                else:
                    return parsed_date.replace(year=datetime.now().year + 1)
            except:
                continue
    
    return None


def parse_time_input(time_text):
    """Парсит время из текстового ввода"""
    
    time_text = time_text.strip().lower()
    
    if time_text in ['весь день', 'в течение дня', 'целый день']:
        return "00:00", "23:59"
    
    # Диапазон времени
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})',  # 09:00-12:00
        r'(\d{1,2})\s*[-–]\s*(\d{1,2})',                     # 9-12
        r'(\d{1,2}):(\d{2})',                                  # 14:30
        r'(\d{1,2})',                                           # 14
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, time_text)
        if match:
            groups = match.groups()
            if len(groups) == 4:  # HH:MM-HH:MM
                start_time = f"{int(groups[0]):02d}:{int(groups[1]):02d}"
                end_time = f"{int(groups[2]):02d}:{int(groups[3]):02d}"
                return start_time, end_time
            elif len(groups) == 2 and ':' in time_text:  # HH:MM
                time_str = f"{int(groups[0]):02d}:{int(groups[1]):02d}"
                return time_str, time_str
            elif len(groups) == 2:  # HH-HH
                start_time = f"{int(groups[0]):02d}:00"
                end_time = f"{int(groups[1]):02d}:00"
                return start_time, end_time
            elif len(groups) == 1:  # HH
                time_str = f"{int(groups[0]):02d}:00"
                return time_str, time_str
    
    return None, None


def handle_schedule_date_input(user_id, text, api: TelegramAPI):
    """Обработка ввода даты для создания расписания"""
    
    user_data = get_user_data()
    
    # Проверяем что у нас есть данные создания расписания
    if (user_id not in user_data or 
        'creating_schedule' not in user_data[user_id]):
        is_admin = db.is_admin(user_id)
        return api.send_message(
            user_id,
            "❌ Данные потеряны. Начните создание записи заново.",
            reply_markup=get_back_button()
        )
    
    # Парсим дату
    parsed_date = parse_date_input(text)
    
    if not parsed_date:
        return api.send_message(
            user_id,
            f"❌ Не удалось распознать дату '{text}'!\n\n"
            f"Попробуйте ввести в одном из форматов:\n"
            f"• `сегодня`, `завтра`\n"
            f"• `{datetime.now().strftime('%d.%m')}`, `{datetime.now().strftime('%d.%m.%Y')}`\n"
            f"• `{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}`\n\n"
            f"Или /cancel для отмены",
            parse_mode='Markdown'
        )
    
    # Сохраняем дату
    user_data[user_id]['creating_schedule']['date'] = parsed_date.strftime('%Y-%m-%d')
    set_user_state(user_id, 'admin_schedule_input_time')
    
    # Переходим к вводу времени
    task_type = user_data[user_id]['creating_schedule']['type']
    username = user_data[user_id]['creating_schedule']['assigned_username']
    type_emoji = get_task_type_emoji(task_type)
    
    return api.send_message(
        user_id,
        f"⏰ *Время выполнения*\n\n"
        f"Задание: {type_emoji} {task_type}\n"
        f"Исполнитель: @{username}\n"
        f"Дата: {parsed_date.strftime('%d.%m.%Y')}\n\n"
        f"Введите время в любом формате:\n"
        f"• `весь день` - на весь день\n"
        f"• `09:00-12:00` - диапазон времени\n"
        f"• `9-12` - упрощенный диапазон\n"
        f"• `14:30` - конкретное время\n\n"
        f"Или /cancel для отмены",
        parse_mode='Markdown'
    )


def handle_schedule_time_input(user_id, text, api: TelegramAPI):
    """Обработка ввода времени для создания расписания"""
    
    user_data = get_user_data()
    
    # Проверяем что у нас есть данные создания расписания
    if (user_id not in user_data or 
        'creating_schedule' not in user_data[user_id]):
        return api.send_message(
            user_id,
            "❌ Данные потеряны. Начните создание записи заново.",
            reply_markup=get_back_button()
        )
    
    # Парсим время
    start_time, end_time = parse_time_input(text)
    
    if not start_time or not end_time:
        return api.send_message(
            user_id,
            f"❌ Не удалось распознать время '{text}'!\n\n"
            f"Попробуйте ввести в одном из форматов:\n"
            f"• `весь день`\n"
            f"• `09:00-12:00`\n"
            f"• `9-12`\n"
            f"• `14:30`\n\n"
            f"Или /cancel для отмены",
            parse_mode='Markdown'
        )
    
    # Сохраняем время
    user_data[user_id]['creating_schedule']['start_time'] = start_time
    user_data[user_id]['creating_schedule']['end_time'] = end_time
    
    task_type = user_data[user_id]['creating_schedule']['type']
    
    # Если это уборка или пересчеты, спрашиваем детали
    if task_type in ['Уборка', 'Пересчеты']:
        detail_type = "стеллажи/полки" if task_type == 'Уборка' else "стеллажи для пересчета"
        set_user_state(user_id, 'admin_schedule_input_details')
        
        username = user_data[user_id]['creating_schedule']['assigned_username']
        date_str = user_data[user_id]['creating_schedule']['date']
        type_emoji = get_task_type_emoji(task_type)
        
        time_display = f"{start_time}-{end_time}" if f"{start_time}-{end_time}" != "00:00-23:59" else "Весь день"
        
        return api.send_message(
            user_id,
            f"📝 *Детали задания*\n\n"
            f"Задание: {type_emoji} {task_type}\n"
            f"Исполнитель: @{username}\n"
            f"Дата: {date_str}\n"
            f"Время: {time_display}\n\n"
            f"Укажите {detail_type}:\n"
            f"• `А1-А5` - диапазон полок\n"
            f"• `Н` - весь стеллаж Н\n"
            f"• `А1, А3, Б2-Б4` - несколько участков\n"
            f"• `все` - все стеллажи\n\n"
            f"Или напишите `пропустить` для стандартного описания\n"
            f"Или /cancel для отмены",
            parse_mode='Markdown'
        )
    else:
        # Для обедов сразу создаем расписание
        return create_schedule_from_data(user_id, api)


def handle_schedule_details_input(user_id, text, api: TelegramAPI):
    """Обработка ввода деталей для расписания"""
    
    user_data = get_user_data()
    
    # Проверяем что у нас есть данные создания расписания
    if (user_id not in user_data or 
        'creating_schedule' not in user_data[user_id]):
        return api.send_message(
            user_id,
            "❌ Данные потеряны. Начните создание записи заново.",
            reply_markup=get_back_button()
        )
    
    # Сохраняем детали
    if text.strip().lower() in ['пропустить', 'skip']:
        user_data[user_id]['creating_schedule']['details'] = None
    else:
        user_data[user_id]['creating_schedule']['details'] = text.strip()
    
    # Создаем расписание
    return create_schedule_from_data(user_id, api)


def create_schedule_from_data(user_id, api: TelegramAPI):
    """Создание расписания из собранных данных"""
    
    user_data = get_user_data()
    schedule_data = user_data[user_id]['creating_schedule']
    
    # Определяем keyboard в начале функции!
    keyboard = [
        [{'text': '➕ Создать еще', 'callback_data': 'admin_schedule_add'}],
        [{'text': '📅 К расписанию', 'callback_data': 'admin_schedule'}],
        [{'text': '🏠 Главное меню', 'callback_data': 'back_main'}]
    ]
    
    # Формируем параметры для сохранения
    assigned_to = schedule_data['assigned_to']
    task_type = schedule_data['type']
    date = schedule_data['date']
    time_slot = f"{schedule_data['start_time']}-{schedule_data['end_time']}"
    shelves = schedule_data.get('details')  # Стеллажи/детали
    
    # РЕАЛЬНО СОЗДАЕМ В БАЗЕ ДАННЫХ!
    try:
        logger.info(f"📋 Создаем запись в YDB: {task_type} для {assigned_to} на {date}")
        
        success, result = db.create_schedule_task(
            user_id=assigned_to,
            task_type=task_type,
            date=date,
            time_slot=time_slot,
            shelves=shelves
        )
        
        if success:
            logger.info(f"✅ Запись создана в YDB: {result}")
            
            # Формируем сообщение об успехе
            type_emoji = get_task_type_emoji(task_type)
            time_display = time_slot if time_slot != "00:00-23:59" else "Весь день"
            
            # Форматируем дату для отображения
            date_parts = date.split('-')
            if len(date_parts) == 3:
                formatted_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
            else:
                formatted_date = date
            
            success_message = (
                f"✅ *Расписание создано и сохранено в базе!*\n\n"
                f"🎯 Тип: {type_emoji} {task_type}\n"
                f"👤 Исполнитель: @{schedule_data['assigned_username']}\n"
                f"📅 Дата: {formatted_date}\n"
                f"⏰ Время: {time_display}\n"
            )
            
            if shelves:
                success_message += f"📝 Детали: {shelves}\n"
            
            success_message += f"\n🎉 Задание добавлено в расписание и базу данных!"
            success_message += f"\n🆔 ID задачи: `{result[:8]}...`"
            
        else:
            logger.error(f"❌ Ошибка создания в YDB: {result}")
            
            success_message = (
                f"❌ *Ошибка создания расписания*\n\n"
                f"Не удалось сохранить в базу данных:\n"
                f"`{result}`\n\n"
                f"Попробуйте еще раз или обратитесь к администратору."
            )
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка создания расписания: {e}")
        import traceback
        traceback.print_exc()
        
        success_message = (
            f"❌ *Критическая ошибка*\n\n"
            f"Произошла ошибка при сохранении:\n"
            f"`{str(e)}`\n\n"
            f"Попробуйте еще раз."
        )
    
    # Очищаем состояние
    set_user_state(user_id, 'main')
    if 'creating_schedule' in user_data[user_id]:
        del user_data[user_id]['creating_schedule']
    
    return api.send_message(
        user_id,
        success_message,
        reply_markup={'inline_keyboard': keyboard},
        parse_mode='Markdown'
    )


def handle_schedule_callback(user_id, message_id, callback_data, api: TelegramAPI):
    """Роутер для callback'ов расписания"""
    
    if callback_data == 'schedule':
        return handle_schedule_menu_callback(user_id, message_id, api)
    
    elif callback_data in ['schedule_meals', 'schedule_cleaning', 'schedule_counting']:
        return handle_schedule_type(user_id, message_id, callback_data, api)
    
    else:
        return api.edit_message(
            user_id,
            message_id,
            f"❓ Функция `{callback_data}` в разработке",
            reply_markup={'inline_keyboard': [[{'text': '◀️ К расписанию', 'callback_data': 'schedule'}]]}
        )