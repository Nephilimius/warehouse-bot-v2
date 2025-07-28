#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модульный Telegram бот - чистый webhook с разделением на хендлеры
"""

import traceback
from flask import Flask, request, jsonify
import json
import logging
import os
import time
from datetime import datetime

# Импорты конфигурации
from config import TOKEN

# Импорты хендлеров
from handlers.utils import TelegramAPI
from handlers.main_handlers import handle_text_message
from handlers.callback_router import handle_callback_query

# Настройки
WEBHOOK_PORT = 8080
WEBHOOK_PATH = f'/{TOKEN}'

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask приложение
app = Flask(__name__)

# Создаем экземпляр Telegram API
telegram_api = TelegramAPI(TOKEN)


@app.before_request
def log_request():
    """Логирование запросов"""
    if request.path == WEBHOOK_PATH:
        logger.info(f"🌐 WEBHOOK: {request.method} {request.content_length or 0} bytes")


@app.route('/', methods=['GET'])
def health_check():
    """Health check"""
    return f"""
🤖 Модульный Telegram Webhook

✅ Работает с чистой архитектурой!
🔗 Webhook: {WEBHOOK_PATH}
🏠 Port: {WEBHOOK_PORT}
🕒 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🏗️ Архитектура:
• Модульная структура хендлеров
• Разделение логики по файлам
• Чистый код без дублирования
• Легкое масштабирование

📁 Структура:
• handlers/main_handlers.py - основные команды
• handlers/task_handlers.py - задачи
• handlers/schedule_handlers.py - расписание
• handlers/notification_handlers.py - уведомления
• handlers/report_handlers.py - отчеты
• handlers/admin_handlers.py - администрация
• handlers/callback_router.py - роутинг
"""


@app.route('/health', methods=['GET'])
def health_json():
    """JSON health check"""
    return jsonify({
        "status": "healthy",
        "architecture": "modular_handlers",
        "webhook_path": WEBHOOK_PATH,
        "port": WEBHOOK_PORT,
        "timestamp": datetime.now().isoformat()
    })


@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Чистый webhook с модульной архитектурой"""
    try:
        # Получаем JSON
        json_data = request.get_json()
        if not json_data:
            logger.error("❌ Пустой JSON")
            return "No JSON", 400
        
        # Обрабатываем message
        if 'message' in json_data:
            msg = json_data['message']
            user_id = msg['from']['id']
            username = msg['from'].get('username', 'unknown')
            text = msg.get('text', '')
            
            logger.info(f"💬 MSG @{username}: {text[:30]}")
            
            success, result = handle_text_message(user_id, username, text, telegram_api)
            
            if success:
                logger.info(f"✅ MESSAGE от @{username} обработан")
                return "OK", 200
            else:
                logger.error(f"❌ Ошибка message: {result}")
                return "Error", 500
        
        # Обрабатываем callback_query
        elif 'callback_query' in json_data:
            cb = json_data['callback_query']
            user_id = cb['from']['id']
            username = cb['from'].get('username', 'unknown')
            callback_data = cb.get('data', '')
            message_id = cb['message']['message_id']
            query_id = cb['id']
            
            logger.info(f"🔘 CB @{username}: {callback_data}")
            
            success, result = handle_callback_query(
                user_id, callback_data, message_id, query_id, telegram_api
            )
            
            if success:
                logger.info(f"✅ CALLBACK от @{username} обработан")
                return "OK", 200
            else:
                logger.error(f"❌ Ошибка callback: {result}")
                return "Error", 500
        
        else:
            logger.warning(f"❓ Неизвестный тип: {list(json_data.keys())}")
            return "Unknown update", 400
            
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        traceback.print_exc()
        return "Critical error", 500


def setup_webhook():
    """Настройка webhook (опционально)"""
    try:
        # Здесь можно добавить логику автонастройки ngrok
        print("🔗 Для настройки webhook используйте ngrok:")
        print(f"   ngrok http {WEBHOOK_PORT}")
        print(f"   Затем установите webhook на Telegram")
        return True
    except Exception as e:
        print(f"⚠️ Ошибка настройки webhook: {e}")
        return False


if __name__ == '__main__':
    print("🚀 ЗАПУСК МОДУЛЬНОГО БОТА")
    print("=" * 40)
    print()
    
    try:
        print("🏗️ Архитектура:")
        print("   ✅ Модульные хендлеры")
        print("   ✅ Чистое разделение логики")
        print("   ✅ Легкое масштабирование")
        print("   ✅ Отсутствие дублирования")
        print()
        print(f"🏠 Host: 0.0.0.0:{WEBHOOK_PORT}")
        print(f"🔗 Webhook: {WEBHOOK_PATH}")
        print()
        
        # Опциональная настройка webhook
        setup_webhook()
        
        print("✅ Запуск Flask...")
        
        app.run(
            host='0.0.0.0',
            port=WEBHOOK_PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        print("✅ Сервер остановлен")
