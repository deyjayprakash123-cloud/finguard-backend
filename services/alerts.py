import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_finguard_alert(user_name: str, score: int, signals: list):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not configured. Mocking alert dispatch:")
        _mock_print_alert(user_name, score, signals)
        return False

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = f"""🚨 FinGuard Alert\n{user_name} has reached a high risk score of {score}%!\nUnusual transaction activity detected."""

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        print("Alert dispatched to Telegram.")
        return True
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Telegram API Response: {e.response.text}")
        return False

def _mock_print_alert(user_name, score, signals):
    msg = f"""
🚨 FinGuard Alert
{user_name} has reached a high risk score of {score}%!
Unusual transaction activity detected.
"""
    print(msg)
