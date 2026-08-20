import datetime
import urllib.parse
import urllib.request
import json
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
TARGET_DATE = datetime.datetime(2026, 10, 25, 0, 0, 0)
TOTAL_SECONDS_WINDOW = 90 * 86400  # 90 days window
ID_FILE = "last_msg_id.txt"

def telegram_api(method, data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    encoded_data = urllib.parse.urlencode(data).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=encoded_data)
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"API Error ({method}): {e}")
        return None

def delete_message(msg_id):
    if not msg_id:
        return
    print(f"Deleting old message ID: {msg_id}")
    telegram_api("deleteMessage", {"chat_id": CHAT_ID, "message_id": msg_id})

def send_message(message):
    res = telegram_api("sendMessage", {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })
    if res and res.get("ok"):
        new_id = res["result"]["message_id"]
        print(f"Sent new message ID: {new_id}")
        return new_id
    return None

# 1. Read old message ID if it exists
old_msg_id = None
if os.path.exists(ID_FILE):
    with open(ID_FILE, "r") as f:
        content = f.read().strip()
        if content.isdigit():
            old_msg_id = int(content)

# 2. Calculate time left
now = datetime.datetime.now()
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
        "📅 Date: 25 October 2026\n\n"
        f"⏳ Progress: `{bar}` {pct}%\n\n"
        "Time Left:\n"
        f"*{days}* Days | *{hours}*h *{mins}*m *{secs}*s\n\n"
        "_Stay focused, revision mode ON!_ 💪"
    )

# 3. Post new message first
new_msg_id = send_message(text)

# 4. Delete the old message if posting was successful
if new_msg_id:
    if old_msg_id:
        delete_message(old_msg_id)
    # Save the new message ID for the next run
    with open(ID_FILE, "w") as f:
        f.write(str(new_msg_id))
