#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ручная настройка webhook когда ngrok уже запущен
"""

import requests
import os
from datetime import datetime


def load_token():
    """Загружает токен"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        print(f"✅ Токен: {token[:10]}...")
        return token
    except:
        print("❌ Ошибка загрузки токена")
        return None


def get_ngrok_url():
    """Получает URL от ngrok"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        data = response.json()
        
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                url = tunnel['public_url']
                print(f"✅ ngrok URL: {url}")
                return url
        
        print("❌ HTTPS туннель не найден")
        return None
    except:
        print("❌ ngrok не доступен на localhost:4040")
        return None


def set_webhook(token, url):
    """Устанавливает webhook"""
    webhook_url = f"{url}/{token}"
    
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    response = requests.post(api_url, json={
        'url': webhook_url,
        'max_connections': 40,
        'allowed_updates': ['message', 'callback_query']
    })
    
    if response.json().get('ok'):
        print(f"✅ Webhook установлен: {webhook_url}")
        return True
    else:
        print(f"❌ Ошибка: {response.json()}")
        return False


def main():
    print("🚀 БЫСТРАЯ НАСТРОЙКА WEBHOOK")
    print("=" * 40)
    
    token = load_token()
    if not token:
        return
    
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("💡 Убедитесь что ngrok запущен: ngrok http 8080")
        return
    
    if set_webhook(token, ngrok_url):
        print("\n🎉 ГОТОВО!")
        print(f"🔗 Webhook: {ngrok_url}/{token}")
        print("\n📋 Теперь запустите бота:")
        print("python bot_modular.py")
    else:
        print("💥 Не удалось установить webhook")


if __name__ == "__main__":
    main()