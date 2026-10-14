"""یک‌بار اجرا شود: python migrate_add_chat.py
ستون telegram_chat_id را به جدول students اضافه می‌کند."""
from app.database import engine

with engine.connect() as conn:
    try:
        conn.exec_driver_sql("ALTER TABLE students ADD COLUMN telegram_chat_id VARCHAR")
        conn.commit()
        print("✅ ستون telegram_chat_id اضافه شد.")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print("ℹ️ ستون از قبل وجود دارد — نیازی به تغییر نبود.")
        else:
            print("❌ خطا:", e)
