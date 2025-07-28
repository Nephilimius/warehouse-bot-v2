# keyboards.py - Клавиатуры и меню бота

from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from config import ROLE_EMOJI

# Главное меню для обычных пользователей
MAIN_MENU = ReplyKeyboardMarkup([
    ['🔍 Найти', '📄 Задания'],
    ['🗓️ Расписание', '📊 Отчеты'],
    ['🔔 Уведомления', '👤 Профиль']
], resize_keyboard=True)

# Главное меню для администраторов
ADMIN_MAIN_MENU = ReplyKeyboardMarkup([
    ['🔍 Найти', '📄 Задания'],
    ['🗓️ Расписание', '📊 Отчеты'],
    ['🔔 Уведомления', '👤 Профиль'],
    ['👑 Администрация']
], resize_keyboard=True)


async def get_user_menu(user_id):
    """Получить меню в зависимости от роли пользователя."""
    from database import is_admin
    
    if await is_admin(user_id):
        return ADMIN_MAIN_MENU
    else:
        return MAIN_MENU


def get_tasks_menu(role):
    """Меню заданий в зависимости от роли."""
    if role in ['ДС', 'ЗДС']:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Мои задания", callback_data='my_tasks')],
            [InlineKeyboardButton("⏳ Ожидающие", callback_data='pending_tasks')],
            [InlineKeyboardButton("✅ Выполненные", callback_data='completed_tasks')],
            [InlineKeyboardButton("➕ Создать задание", callback_data='create_task')],
            [InlineKeyboardButton("📊 Общая статистика", callback_data='all_stats')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Мои задания", callback_data='my_tasks')],
            [InlineKeyboardButton("⏳ Ожидающие", callback_data='pending_tasks')],
            [InlineKeyboardButton("✅ Выполненные", callback_data='completed_tasks')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
        ])


def get_schedule_menu(role):
    """Меню расписания в зависимости от роли."""
    if role in ['ДС', 'ЗДС']:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🍽️ Обеды", callback_data='schedule_meals')],
            [InlineKeyboardButton("🧹 Уборка", callback_data='schedule_cleaning')],
            [InlineKeyboardButton("🔢 Пересчеты", callback_data='schedule_counting')],
            [InlineKeyboardButton("👥 График сотрудников", callback_data='work_schedule')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🍽️ Обеды", callback_data='schedule_meals')],
            [InlineKeyboardButton("🧹 Уборка", callback_data='schedule_cleaning')],
            [InlineKeyboardButton("🔢 Пересчеты", callback_data='schedule_counting')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
        ])


def get_notifications_menu(role):
    """Меню уведомлений в зависимости от роли."""
    if role in ['ДС', 'ЗДС']:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Мои настройки", callback_data='my_notif_settings')],
            [InlineKeyboardButton("📢 Общие уведомления", callback_data='general_notifications')],
            [InlineKeyboardButton("👥 Настройки сотрудников", callback_data='staff_notifications')],
            [InlineKeyboardButton("📈 История уведомлений", callback_data='notification_history')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Мои настройки", callback_data='my_notif_settings')],
            [InlineKeyboardButton("📢 Общие уведомления", callback_data='general_notifications')],
            [InlineKeyboardButton("📈 История уведомлений", callback_data='notification_history')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
        ])


def get_reports_menu():
    """Меню отчетов."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Качество работы", callback_data='quality_report')],
        [InlineKeyboardButton("⏱️ Время выполнения", callback_data='time_report')],
        [InlineKeyboardButton("🍽️ Отчет по обедам", callback_data='meals_report')],
        [InlineKeyboardButton("🧹 Отчет по уборке", callback_data='cleaning_report')],
        [InlineKeyboardButton("🔢 Отчет по пересчетам", callback_data='counting_report')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_main')]
    ])


def get_admin_menu():
    """Административное меню."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Список пользователей", callback_data='admin_list_users')],
        [InlineKeyboardButton("🎭 Изменить роль", callback_data='admin_change_role')],
        [InlineKeyboardButton("📅 Управление расписанием", callback_data='admin_schedule')],
        [InlineKeyboardButton("🗑️ Удалить пользователя", callback_data='admin_delete_user')],
        [InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("❌ Закрыть", callback_data='admin_close')]
    ])


def get_back_to_main_menu():
    """Кнопка возврата в главное меню."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Главное меню", callback_data='back_main')]
    ])


def get_admin_back_menu():
    """Кнопка возврата к админ панели."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад к админке", callback_data='admin_back')]
    ])


def get_user_selection_keyboard(users):
    """Клавиатура выбора пользователя."""
    buttons = []
    for user in users:
        role_emoji = ROLE_EMOJI.get(user['role'], "👤")
        buttons.append([InlineKeyboardButton(
            f"{role_emoji} @{user['username']}", 
            callback_data=f"select_user_{user['telegram_id']}"
        )])
    
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data='cancel_add_task')])
    return InlineKeyboardMarkup(buttons)


def get_time_slots_keyboard():
    """Клавиатура временных слотов."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("В течение дня", callback_data='time_slot_allday')],
        [InlineKeyboardButton("09:00-12:00", callback_data='time_slot_morning')],
        [InlineKeyboardButton("12:00-15:00", callback_data='time_slot_lunch')],
        [InlineKeyboardButton("15:00-18:00", callback_data='time_slot_afternoon')],
        [InlineKeyboardButton("18:00-21:00", callback_data='time_slot_evening')],
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel_add_task')]
    ])


def get_back_to_tasks():
    """Кнопка возврата к заданиям."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад к заданиям", callback_data='back_tasks')]
    ])


def get_back_to_schedule():
    """Кнопка возврата к расписанию."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад к расписанию", callback_data='back_schedule')]
    ])


def get_back_to_reports():
    """Кнопка возврата к отчетам."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад к отчетам", callback_data='back_reports')]
    ])


def get_back_to_notifications():
    """Кнопка возврата к уведомлениям."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад к уведомлениям", callback_data='back_notifications')]
    ])


def get_task_types_keyboard():
    """Клавиатура выбора типа задания."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍽️ Обеды", callback_data='create_task_meals')],
        [InlineKeyboardButton("🧹 Уборка", callback_data='create_task_cleaning')],
        [InlineKeyboardButton("🔢 Пересчеты", callback_data='create_task_counting')],
        [InlineKeyboardButton("❌ Отмена", callback_data='back_tasks')]
    ])


def get_time_selection_keyboard():
    """Клавиатура выбора времени для задания."""
    from datetime import datetime, timedelta
    
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕘 Сегодня 9:00", callback_data=f'task_time_{today.strftime("%Y-%m-%d")}_09:00')],
        [InlineKeyboardButton("🕐 Сегодня 13:00", callback_data=f'task_time_{today.strftime("%Y-%m-%d")}_13:00')],
        [InlineKeyboardButton("🕕 Сегодня 18:00", callback_data=f'task_time_{today.strftime("%Y-%m-%d")}_18:00')],
        [InlineKeyboardButton("📅 Завтра 9:00", callback_data=f'task_time_{tomorrow.strftime("%Y-%m-%d")}_09:00')],
        [InlineKeyboardButton("📅 Завтра 13:00", callback_data=f'task_time_{tomorrow.strftime("%Y-%m-%d")}_13:00')],
        [InlineKeyboardButton("❌ Отмена", callback_data='back_tasks')]
    ])


def get_task_action_keyboard(task_id, user_role='Кладовщик'):
    """Клавиатура действий с заданием."""
    keyboard = []
    
    if user_role in ['ДС', 'ЗДС']:
        keyboard.extend([
            [InlineKeyboardButton("✏️ Редактировать", callback_data=f'edit_task_{task_id}')],
            [InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_task_{task_id}')]
        ])
    
    keyboard.extend([
        [InlineKeyboardButton("✅ Выполнить", callback_data=f'complete_task_{task_id}')],
        [InlineKeyboardButton("⏸️ В работу", callback_data=f'start_task_{task_id}')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_tasks')]
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_rating_keyboard(task_id):
    """Клавиатура оценки выполненного задания."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐", callback_data=f'rate_task_{task_id}_1'),
            InlineKeyboardButton("⭐⭐", callback_data=f'rate_task_{task_id}_2'),
            InlineKeyboardButton("⭐⭐⭐", callback_data=f'rate_task_{task_id}_3')
        ],
        [
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f'rate_task_{task_id}_4'),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f'rate_task_{task_id}_5')
        ],
        [InlineKeyboardButton("❌ Пропустить", callback_data='back_tasks')]
    ])


def get_task_completion_keyboard():
    """Клавиатура завершения задания."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Прикрепить фото", callback_data='attach_photo_prompt')],
        [InlineKeyboardButton("✅ Завершить без фото", callback_data='complete_without_photo')],
        [InlineKeyboardButton("❌ Отмена", callback_data='back_tasks')]
    ])


def get_shelves_selection_keyboard():
    """Клавиатура выбора стеллажей."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("А1-А5", callback_data='shelves_A1-A5'),
            InlineKeyboardButton("Б1-Б5", callback_data='shelves_B1-B5')
        ],
        [
            InlineKeyboardButton("В1-В5", callback_data='shelves_V1-V5'),
            InlineKeyboardButton("Г1-Г5", callback_data='shelves_G1-G5')
        ],
        [
            InlineKeyboardButton("Все стеллажи", callback_data='shelves_all'),
            InlineKeyboardButton("Другое", callback_data='shelves_custom')
        ],
        [InlineKeyboardButton("❌ Пропустить", callback_data='shelves_skip')]
    ])

def get_admin_schedule_menu():
    """Административное меню управления расписанием."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👀 Просмотр всех записей", callback_data='admin_schedule_view_all')],
        [InlineKeyboardButton("🟢 Добавить запись", callback_data='admin_schedule_add')],
        [InlineKeyboardButton("🗑️ Удалить записи", callback_data='admin_schedule_delete')],
        [InlineKeyboardButton("🍽️ Просмотр обедов", callback_data='admin_schedule_view_meals')],
        [InlineKeyboardButton("🧹 Просмотр уборки", callback_data='admin_schedule_view_cleaning')],
        [InlineKeyboardButton("🔢 Просмотр пересчетов", callback_data='admin_schedule_view_counting')],
        [InlineKeyboardButton("◀️ К админке", callback_data='admin_back')]
    ])


def get_delete_type_menu():
    """Меню выбора типа записей для удаления."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍽️ Удалить обеды", callback_data='admin_delete_meals')],
        [InlineKeyboardButton("🧹 Удалить уборку", callback_data='admin_delete_cleaning')],
        [InlineKeyboardButton("🔢 Удалить пересчеты", callback_data='admin_delete_counting')],
        [InlineKeyboardButton("🗑️ Удалить все типы", callback_data='admin_delete_all_types')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_schedule')]
    ])


def get_delete_confirmation_keyboard(item_id):
    """Клавиатура подтверждения удаления."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f'confirm_delete_{item_id}')],
        [InlineKeyboardButton("❌ Отмена", callback_data=f'cancel_delete_{item_id}')]
    ])
