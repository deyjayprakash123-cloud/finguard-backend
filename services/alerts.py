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
    
    # Format list of signals properly
    signals_str = ", ".join(signals) if signals else "None detected"
    
    message = f"""<b>🚨 FIN-GUARD CRITICAL ALERT 🚨</b>

<b>User:</b> {user_name} | <b>Risk Score:</b> {score}/100

<b>Triggered Signals:</b> {signals_str}

<b>Action Required:</b> Urgent intervention recommended."""

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
    signals_str = ", ".join(signals) if signals else "None detected"
    msg = f"""
🚨 FIN-GUARD CRITICAL ALERT 🚨
User: {user_name} | Risk Score: {score}/100
Triggered Signals: {signals_str}
Action Required: Urgent intervention recommended.
"""
    print(msg)
