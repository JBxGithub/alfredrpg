"""
重置 Telegram Bot Webhook
"""
import requests

BOT_TOKEN = '8577625613:AAFxqb8WFWLJ4Gcl-9UOiqbPvI_0Uqc9rMs'

# 刪除 webhook
delete_webhook_url = f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook'
response = requests.get(delete_webhook_url)
print(f"Delete Webhook: {response.json()}")

# 獲取 webhook 資訊
get_webhook_url = f'https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo'
response = requests.get(get_webhook_url)
print(f"Webhook Info: {response.json()}")

# 獲取 Bot 資訊
get_me_url = f'https://api.telegram.org/bot{BOT_TOKEN}/getMe'
response = requests.get(get_me_url)
print(f"Bot Info: {response.json()}")
