import datetime
import time
import urllib.parse
import urllib.request
import json
import os
from zoneinfo import ZoneInfo

# Telegram secrets from GitHub repository settings
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# GitHub self-relaunch settings (provided automatically by Actions,
# except WORKFLOW_FILE which is set explicitly in the workflow env)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
GITHUB_REF_NAME = os.environ.get("GITHUB_REF_NAME", "main")
WORKFLOW_FILE = os.environ.get("WORKFLOW_FILE", "update.yml")

# Set timezone explicitly to Indian Standard Time (IST)
IST = ZoneInfo("Asia/Kolkata")

# Target: 25 October 2026 at 11:00:00 AM IST
TARGET_DATE = datetime.datetime(2026, 10, 25, 11, 0, 0, tzinfo=IST)
TOTAL_SECONDS_WINDOW = 90 * 86400  # 90-day progress window baseline

LOOP_SECONDS = 60
MAX_RUN_SECONDS = 5 * 3600 + 50 * 60  # 5h50m, safely under the 6h job cap
MSG_ID_FILE = "last_msg_id.txt"


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


def build_text():
    now = datetime.datetime.now(IST)
    diff = int((TARGET_DATE - now).total_seconds())

    if diff <= 0:
        return "🚨 The BPSC 72nd Prelims Exam is TODAY! Best of luck! 🚀📚", diff

    # Calendar days difference
    days = (TARGET_DATE.date() - now.date()).days
    if now.hour >= 11:
        days -= 1

    sub_diff = int((TARGET_DATE - now).total_seconds())
    hours = (sub_diff % 86400) // 3600
    mins = (sub_diff % 3600) // 60
    secs = sub_diff % 60

    fraction = min(max(diff / TOTAL_SECONDS_WINDOW, 0), 1)
    total_blocks = 10
    filled = int((1 - fraction) * total_blocks)
    bar = "█" * filled + "░" * (total_blocks - filled)
    pct = int((1 - fraction) * 100)

    text = (
        "📚 *BPSC 72nd Prelims Countdown* 📚\n"
        "📅 Target: 25 October 2026, 11:00 AM\n\n"
        f"⏳ Progress: `{bar}` {pct}%\n\n"
        "Time Left:\n"
        f"*{days}* Days | *{hours}*h *{mins}*m *{secs}*s\n\n"
        "_Stay focused, revision mode ON!_ 💪"
    )
    return text, diff


def get_msg_id():
    if os.path.exists(MSG_ID_FILE):
        with open(MSG_ID_FILE, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return None


def save_msg_id(msg_id):
    with open(MSG_ID_FILE, "w") as f:
        f.write(str(msg_id))


def send_or_edit(msg_id):
    text, diff = build_text()

    if msg_id is None:
        res = telegram_api("sendMessage", {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        })
        if res and res.get("ok"):
            new_id = res["result"]["message_id"]
            save_msg_id(new_id)
            print(f"Sent new message, id={new_id}")
            return new_id, diff
        print("Failed to send new message.")
        return None, diff

    res = telegram_api("editMessageText", {
        "chat_id": CHAT_ID,
        "message_id": msg_id,
        "text": text,
        "parse_mode": "Markdown"
    })
    if res is None or res.get("ok") or "message is not modified" in json.dumps(res):
        print(f"Edited message id={msg_id}")
    else:
        print(f"Edit failed: {res}")
    return msg_id, diff


def relaunch_workflow():
    if not (GITHUB_TOKEN and GITHUB_REPOSITORY):
        print("Missing GITHUB_TOKEN/GITHUB_REPOSITORY, cannot self-relaunch.")
        return
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    body = json.dumps({"ref": GITHUB_REF_NAME}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "bpsc-countdown-bot")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        print(f"Relaunch dispatch status={resp.status}")
    except Exception as e:
        print(f"Relaunch dispatch failed: {e}")


def main():
    start = time.monotonic()
    msg_id = get_msg_id()

    while True:
        msg_id, diff = send_or_edit(msg_id)

        if diff <= 0:
            print("Countdown finished, stopping loop.")
            return

        if time.monotonic() - start > MAX_RUN_SECONDS:
            relaunch_workflow()
            return

        time.sleep(LOOP_SECONDS)


if __name__ == "__main__":
    main()
