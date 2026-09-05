from datetime import date
from app.database import SessionLocal
from app.models import Student, Grade, Attendance

db = SessionLocal()

# دانش‌آموز دوم: افت تحصیلی در علوم
sara = Student(name="سارا کریمی", class_name="هشتم ۲", parent_name="زهرا کریمی")
db.add(sara)
db.commit()
db.refresh(sara)

db.add_all([
    Grade(student_id=sara.id, subject="علوم", score=18, date=date(2026, 6, 1)),
    Grade(student_id=sara.id, subject="علوم", score=11, date=date(2026, 7, 1)),
    Grade(student_id=sara.id, subject="ریاضی", score=14, date=date(2026, 6, 1)),
    Grade(student_id=sara.id, subject="ریاضی", score=13, date=date(2026, 7, 1)),
])
db.add_all([
    Attendance(student_id=sara.id, date=date(2026, 8, 1), status="absent"),
    Attendance(student_id=sara.id, date=date(2026, 8, 2), status="absent"),
    Attendance(student_id=sara.id, date=date(2026, 8, 3), status="absent"),
])

# دانش‌آموز سوم: وضعیت پایدار و خوب
mohammad = Student(name="محمد احمدی", class_name="هشتم ۱", parent_name="احمد احمدی")
db.add(mohammad)
db.commit()
db.refresh(mohammad)

db.add_all([
    Grade(student_id=mohammad.id, subject="ریاضی", score=19, date=date(2026, 6, 1)),
    Grade(student_id=mohammad.id, subject="ریاضی", score=19, date=date(2026, 7, 1)),
])
db.add_all([
    Attendance(student_id=mohammad.id, date=date(2026, 8, 1), status="present"),
    Attendance(student_id=mohammad.id, date=date(2026, 8, 2), status="present"),
])

db.commit()
db.close()

print("✅ دانش‌آموزان اضافه با موفقیت ثبت شدند.")