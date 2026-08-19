import datetime
import urllib.parse
import urllib.request
import json
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
TARGET_DATE = datetime.datetime(2026, 10, 25, 0, 0, 0)
TOTAL_SECONDS_WINDOW = 90 * 86400  # 90 days window

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req)
        print("Successfully sent countdown update to Telegram!")
    except Exception as e:
        print(f"Error sending message: {e}")

# Calculate time left
now = datetime.datetime.now()
diff = int((TARGET_DATE - now).total_seconds())

if diff <= 0:
    text = "🚨 The BPSC 72nd Prelims Exam is TODAY! Best of luck! 🚀📚"
else:
    days = diff // 86400
    hours = (diff % 86400) // 3600
    mins = (diff % 3600) // 60
    
    # Simple progress calculation
    fraction = min(max(diff / TOTAL_SECONDS_WINDOW, 0), 1)
    total_blocks = 10
    filled = int((1 - fraction) * total_blocks)
    bar = "█" * filled + "░" * (total_blocks - filled)
    pct = int((1 - fraction) * 100)

    text = (
        "📚 *BPSC 72nd Prelims Countdown* 📚\n"
        "📅 Date: 25 October 2026\n\n"
        f"⏳ Progress: `{bar}` {pct}%\n\n"
        "Time Left:\n"
        f"*{days}* Days | *{hours}*h *{mins}*m\n\n"
        "_Stay focused, revision mode ON!_ 💪"
    )

send_telegram_message(text)
