"""اطلاع‌رسانی تلگرام — گزارش‌های تأییدشده به والد خصوصی یا گروه مدرسه."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PROXY = os.getenv("TELEGRAM_PROXY") or None
PROXIES = {"http": PROXY, "https": PROXY} if PROXY else None


class TelegramError(Exception):
    """خطای مربوط به ارسال پیام تلگرام."""


def send_telegram_message(text: str) -> dict:
    """ارسال پیام به گروه/کانال مشترک مدرسه."""
    if not TELEGRAM_ENABLED:
        return {"status": "disabled"}
    if not BOT_TOKEN or not CHAT_ID:
        raise TelegramError("TELEGRAM_BOT_TOKEN یا TELEGRAM_CHAT_ID در .env تنظیم نشده است.")
    return send_to_chat(CHAT_ID, text)


def send_to_chat(chat_id: str, text: str) -> dict:
    """ارسال به یک چت مشخص (والد یا گروه)."""
    if not BOT_TOKEN:
        raise TelegramError("TELEGRAM_BOT_TOKEN تنظیم نشده است.")
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=30,
            proxies=PROXIES,
        )
    except requests.RequestException as e:
        raise TelegramError(f"خطا در اتصال به api.telegram.org: {e}")
    data = response.json()
    if not data.get("ok"):
        raise TelegramError(f"تلگرام خطا داد: {data.get('description')}")
    return data


def notify_approved_report(student_name: str, report_text: str) -> dict:
    """اعلان گزارش تأییدشده به گروه مدرسه."""
    text = f"📋 گزارش تأییدشده — {student_name}\n\n{report_text}"
    return send_telegram_message(text)


def notify_parent(student, report_text: str) -> str:
    """گزارش را به والدِ خصوصی می‌فرستد؛ اگر والد وصل نباشد به گروه می‌رود.
    خروجی: وضعیت ارسال (sent_to_parent / sent_to_group_fallback / no_destination)"""
    header = f"📋 گزارش وضعیت — {student.name}\n\n{report_text}"

    if getattr(student, "telegram_chat_id", None):
        send_to_chat(student.telegram_chat_id, header)
        return "sent_to_parent"

    if TELEGRAM_ENABLED and CHAT_ID:
        send_telegram_message(f"⚠️ والد {student.name} هنوز به ربات وصل نشده است.\n\n{header}")
        return "sent_to_group_fallback"

    return "no_destination"

