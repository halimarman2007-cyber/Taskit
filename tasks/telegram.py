import requests
from django.conf import settings

def send_telegram_message(chat_id, message):
    print("BOT TOKEN:", settings.TELEGRAM_BOT_TOKEN)  # DEBUG
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, data=data)
    print("Telegram response:", response.text)  # DEBUG
