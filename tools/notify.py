#!/usr/bin/env python3
"""
notify.py — send a short notification about a cpg_book -> Supabase sync.

Provider-agnostic and fail-soft: it sends to whichever channel is configured via
environment variables, and exits 0 (without error) when none is set, so it never
breaks a CI run. Pick a channel by setting ONE of:

  Discord   : DISCORD_WEBHOOK_URL
  Telegram  : TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
  LINE      : LINE_CHANNEL_ACCESS_TOKEN + LINE_TO   (Messaging API push)

Usage:  python notify.py "ข้อความแจ้งเตือน"
"""
import json, os, sys, urllib.request


def _post(url, payload, headers):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status


def send(msg):
    if os.environ.get("DISCORD_WEBHOOK_URL"):
        return "discord", _post(os.environ["DISCORD_WEBHOOK_URL"], {"content": msg}, {})
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage"
        return "telegram", _post(url, {"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": msg}, {})
    if os.environ.get("LINE_CHANNEL_ACCESS_TOKEN") and os.environ.get("LINE_TO"):
        return "line", _post(
            "https://api.line.me/v2/bot/message/push",
            {"to": os.environ["LINE_TO"], "messages": [{"type": "text", "text": msg}]},
            {"Authorization": "Bearer " + os.environ["LINE_CHANNEL_ACCESS_TOKEN"]})
    return None, None


def main():
    msg = " ".join(sys.argv[1:]) or "cpg_book sync"
    try:
        channel, status = send(msg)
    except Exception as e:
        print(f"[notify] send failed (ignored): {e}")
        return
    if channel:
        print(f"[notify] sent via {channel} -> HTTP {status}")
    else:
        print("[notify] no channel configured — set DISCORD_WEBHOOK_URL / TELEGRAM_* / LINE_*")


if __name__ == "__main__":
    main()
