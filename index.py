"""
index.py - Главный обработчик для Yandex Cloud Functions

Обрабатывает входящие webhook'и от Telegram и маршрутизирует их
к соответствующим обработчикам команд и callback'ов.
"""

import json
import logging
import os
from handlers.utils import TelegramAPI
from handlers.main_handlers import handle_text_message
from handlers.callback_router import handle_callback_query

# Настройка логирования для Cloud Functions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event, context):
    """Главный обработчик для Yandex Cloud Functions"""
    print("🚀 ФУНКЦИЯ ЗАПУЩЕНА!")
    print(f"📥 Raw event: {event}")
    
    try:
        # Получаем токен из переменных окружения
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        print(f"🔑 Token found: {bool(token)}")
        
        if not token:
            print("❌ TOKEN НЕ НАЙДЕН!")
            logger.error(
                "❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения"
            )
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Token not found'})
            }
        
        print("✅ Создаем TelegramAPI...")
        # Создаем API объект
        telegram_api = TelegramAPI(token)
        print("✅ TelegramAPI создан!")
        
        # Парсим входящий JSON
        print("📄 Парсим JSON...")
        try:
            if isinstance(event.get('body'), str):
                print("📄 Body - строка, парсим JSON...")
                update_data = json.loads(event['body'])
            else:
                print("📄 Body - уже объект...")
                update_data = event.get('body', {})
                
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid JSON'})
            }
        
        print(f"📥 Parsed update: {update_data}")
        logger.info(f"📥 Получен update: {update_data}")
        
        # Обрабатываем message
        if 'message' in update_data:
            print("💬 Обрабатываем MESSAGE...")
            msg = update_data['message']
            user_id = msg['from']['id']
            username = msg['from'].get('username', 'unknown')
            text = msg.get('text', '')
            
            print(f"💬 MESSAGE от @{username} (ID: {user_id}): {text}")
            logger.info(f"💬 MESSAGE от @{username}: {text[:30]}")
            
            print("🔄 Вызываем handle_text_message...")
            success, result = handle_text_message(
                user_id, username, text, telegram_api
            )
            print(f"🔄 handle_text_message результат: success={success}, result={result}")
            
            if success:
                print("✅ MESSAGE успешно обработан!")
                logger.info(f"✅ MESSAGE обработан")
                return {
                    'statusCode': 200,
                    'body': json.dumps({'status': 'ok', 'type': 'message'})
                }
            else:
                print(f"❌ Ошибка обработки MESSAGE: {result}")
                logger.error(f"❌ Ошибка обработки message: {result}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': str(result)})
                }
        
        # Обрабатываем callback_query
        elif 'callback_query' in update_data:
            print("🔘 Обрабатываем CALLBACK...")
            cb = update_data['callback_query']
            user_id = cb['from']['id']
            username = cb['from'].get('username', 'unknown')
            callback_data = cb.get('data', '')
            message_id = cb['message']['message_id']
            query_id = cb['id']
            
            print(f"🔘 CALLBACK от @{username} (ID: {user_id}): {callback_data}")
            logger.info(f"🔘 CALLBACK от @{username}: {callback_data}")
            
            print("🔄 Вызываем handle_callback_query...")
            success, result = handle_callback_query(
                user_id, callback_data, message_id, query_id, telegram_api
            )
            print(
                f"🔄 handle_callback_query результат: "
                f"success={success}, result={result}"
            )
            
            if success:
                print("✅ CALLBACK успешно обработан!")
                logger.info(f"✅ CALLBACK обработан")
                return {
                    'statusCode': 200,
                    'body': json.dumps({'status': 'ok', 'type': 'callback'})
                }
            else:
                print(f"❌ Ошибка обработки CALLBACK: {result}")
                logger.error(f"❌ Ошибка обработки callback: {result}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': str(result)})
                }
        
        else:
            update_keys = list(update_data.keys())
            print(f"❓ Неизвестный тип update: {update_keys}")
            logger.warning(f"❓ Неизвестный тип update: {update_keys}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unknown update type'})
            }
            
    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Critical error', 
                'details': str(e)
            })
        }