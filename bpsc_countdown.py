import datetime
import urllib.parse
import urllib.request
import json
import os
from zoneinfo import ZoneInfo

# Telegram secrets from GitHub repository settings
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Set timezone explicitly to Indian Standard Time (IST)
IST = ZoneInfo("Asia/Kolkata")

# Target: 25 October 2026 at 11:00:00 AM IST
TARGET_DATE = datetime.datetime(2026, 10, 25, 11, 0, 0, tzinfo=IST)
TOTAL_SECONDS_WINDOW = 90 * 86400  # 90-day progress window baseline

def telegram_api(method, data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    encoded_data = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=encoded_data)
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Telegram API Error ({method}): {e}")
        return None

def main():
    # Get current exact time in IST
    now = datetime.datetime.now(IST)
    diff = int((TARGET_DATE - now).total_seconds())

    if diff <= 0:
        text = "🚨 The BPSC 72nd Prelims Exam is TODAY! Best of luck! 🚀📚"
    else:
        days = diff // 86400
        hours = (diff % 86400) // 3600
        mins = (diff % 3600) // 60
        secs = diff % 60
        
        fraction = min(max(diff / TOTAL_SECONDS_WINDOW, 0), 1)
        total_blocks = 10
        filled = int((1 - fraction) * total_blocks)
        bar = "█" * filled + "░" * (total_blocks - filled)
        pct = int((1 - fraction) * 100)

        text = (
            "📚 *BPSC 72nd Prelims Countdown* 📚\n"
            "📅 Target: 25 October 2026, 11:00 AM IST\n\n"
            f"⏳ Progress: `{bar}` {pct}%\n\n"
            "Time Left:\n"
            f"*{days}* Days | *{hours}*h *{mins}*m *{secs}*s\n\n"
            "_Stay focused, revision mode ON!_ 💪"
        )

    # File tracking for message auto-deletion
    filename = "last_msg_id.txt"
    old_msg_id = None
    if os.path.exists(filename):
        with open(filename, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                old_msg_id = int(content)

    # Send new message
    res = telegram_api("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })

    if res and res.get("ok"):
        new_msg_id = res["result"]["message_id"]
        
        # Delete old message if it exists
        if old_msg_id:
            telegram_api("deleteMessage", {
                "chat_id": CHAT_ID,
                "message_id": old_msg_id
            })

        # Save new message ID
        with open(filename, "w") as f:
            f.write(str(new_msg_id))
        print(f"Successfully updated! New message ID: {new_msg_id}")
    else:
        print("Failed to send new message.")

if __name__ == "__main__":
    main()
