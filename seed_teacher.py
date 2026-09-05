from app.database import SessionLocal
from app.models import Teacher
from app.auth import hash_password

db = SessionLocal()

teacher = Teacher(
    name="خانم احمدی",
    username="teacher1",
    hashed_password=hash_password("1234"),
    subject="ریاضی",
    class_name="هشتم 2",
)
db.add(teacher)
db.commit()
db.close()

print("✅ معلم نمونه ثبت شد.")
