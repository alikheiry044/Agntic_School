"""ربات شنونده — اجرا: python bot_listener.py (در ترمینال جدا از uvicorn)"""
import time, requests
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

def tg(method, **data):
    return requests.post(f"{API}/{method}", json=data, timeout=30).json()

def handle(msg):
    chat_id = str(msg["chat"]["id"])
    text = (msg.get("text") or "").strip()

    if text.startswith("/start") or text == "راهنما":
        tg("sendMessage", chat_id=chat_id,
           text="سلام! برای دریافت گزارش فرزندتان این را بفرستید:\n\nپیوند <شناسه دانش‌آموز> <رمز>\n\nمثال: پیوند 3 1234")
        return

    if text.startswith("پیوند"):
        parts = text.split()
        if len(parts) != 3 or not parts[1].isdigit():
            tg("sendMessage", chat_id=chat_id, text="فرمت درست: پیوند 3 1234")
            return
        from app.database import SessionLocal
        from app.models import Student
        db = SessionLocal()
        try:
            stu = db.query(Student).filter(Student.id == int(parts[1])).first()
            if not stu:
                tg("sendMessage", chat_id=chat_id, text="❌ دانش‌آموزی با این شناسه پیدا نشد.")
                return
            from app.auth import verify_password
            if not verify_password(parts[2], stu.hashed_password or ""):
                tg("sendMessage", chat_id=chat_id, text="❌ رمز اشتباه است.")
                return
            stu.telegram_chat_id = chat_id
            db.commit()
            tg("sendMessage", chat_id=chat_id,
               text=f"✅ وصل شد! گزارش‌های «{stu.name}» از این به بعد همین‌جا ارسال می‌شود.")
        finally:
            db.close()
    else:
        tg("sendMessage", chat_id=chat_id, text="برای شروع بنویسید: /start")

offset = 0
print("🤖 ربات در حال شنیدن...")
while True:
    try:
        res = tg("getUpdates", offset=offset, timeout=30)
        for upd in res.get("result", []):
            offset = upd["update_id"] + 1
            if "message" in upd:
                handle(upd["message"])
    except Exception as e:
        print("خطا:", e)
        time.sleep(3)