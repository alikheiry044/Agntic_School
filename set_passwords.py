from app.database import SessionLocal
from app.models import Student
from app.auth import hash_password

db = SessionLocal()

# برای دموی فعلی، پسورد همه دانش‌آموزان رو یکسان می‌ذاریم: 1234
# در محصول واقعی، هر خانواده باید پسورد اختصاصی خودش رو داشته باشه
students = db.query(Student).all()

for s in students:
    s.hashed_password = hash_password("1234")

db.commit()
db.close()

print(f"✅ پسورد برای {len(students)} دانش‌آموز تنظیم شد.")
