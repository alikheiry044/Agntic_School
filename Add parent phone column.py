"""
یک بار اجرا کن تا فیلد parent_phone به جدول students توی school.db اضافه بشه،
بدون اینکه داده‌های فعلی پاک بشن (چون از Base.metadata.create_all استفاده نمی‌کنه، مستقیم ALTER TABLE می‌زنه).

اجرا:
    python add_parent_phone_column.py
"""

import sqlite3

DB_PATH = "school.db"


def column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    if column_exists(cur, "students", "parent_phone"):
        print("✅ ستون parent_phone از قبل وجود داره، کاری لازم نیست.")
    else:
        cur.execute("ALTER TABLE students ADD COLUMN parent_phone VARCHAR")
        con.commit()
        print("✅ ستون parent_phone به جدول students اضافه شد.")

    con.close()


if __name__ == "__main__":
    main()