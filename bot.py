import datetime
import urllib.parse
import urllib.request
import json
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
TARGET_DATE = datetime.datetime(2026, 10, 25, 0, 0, 0)
TOTAL_SECONDS_WINDOW = 90 * 86400

current_msg_id = None

# --- Tiny web server to satisfy Render's port requirement ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"BPSC Countdown Bot is running!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()
# -------------------------------------------------------------

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

def countdown_loop():
    global current_msg_id
    print("BPSC Countdown 24/7 Cloud Bot Started...")
    
    while True:
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

        new_msg_id = send_message(text)

        if new_msg_id:
            if current_msg_id:
                delete_message(current_msg_id)
            current_msg_id = new_msg_id

        time.sleep(3600)

if __name__ == "__main__":
    # Start the web server in a background thread so Render detects an open port
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    # Run the countdown loop in the main thread
    countdown_loop()
