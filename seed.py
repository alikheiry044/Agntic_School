"""ساخت دیتابیس اولیه — python seed.py
⚠️ فقط یک‌بار اجرا شود! قبل از اجرا، فایل school.db را حذف کن."""
from datetime import date
from app.database import Base, engine, SessionLocal
from app.models import Student, Teacher, Grade, Attendance, Exam, Tuition
from app.auth import hash_password

# قدم ۱: ساخت واقعی جدول‌ها
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ===== قدم ۲: دانش‌آموزان نمونه (رمز والد همه: 1234) =====
def add_student(name, class_name, parent_name):
    s = Student(
        name=name,
        class_name=class_name,
        parent_name=parent_name,
        hashed_password=hash_password("1234"),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

ali = add_student("علی رضایی", "هشتم ۲", "مریم رضایی")
sara = add_student("سارا کریمی", "هشتم ۲", "زهرا کریمی")
mohammad = add_student("محمد احمدی", "هشتم ۱", "احمد احمدی")
maryam = add_student("مریم حسینی", "نهم ۲", "جواد حسینی")

# ===== قدم ۳: معلم نمونه (teacher1 / 1234) =====
# ⚠️ کلاس معلم باید «دقیقاً» مثل کلاس دانش‌آموزان باشد (هشتم ۲ با عدد فارسی)
db.add(Teacher(
    name="خانم احمدی",
    subject="ریاضی",
    class_name="هشتم ۲",
    username="teacher1",
    hashed_password=hash_password("1234"),
))

# ===== قدم ۴: نمرات — علی افت در ریاضی، سارا افت در دو درس، مریم افت در ادبیات =====
db.add_all([
    Grade(student_id=ali.id, subject="ریاضی", score=15, date=date(2026, 6, 1)),
    Grade(student_id=ali.id, subject="ریاضی", score=17, date=date(2026, 7, 1)),
    Grade(student_id=ali.id, subject="علوم", score=12, date=date(2026, 7, 5)),

    Grade(student_id=sara.id, subject="ریاضی", score=17, date=date(2026, 6, 1)),
    Grade(student_id=sara.id, subject="ریاضی", score=11, date=date(2026, 7, 1)),
    Grade(student_id=sara.id, subject="علوم", score=16, date=date(2026, 6, 10)),
    Grade(student_id=sara.id, subject="علوم", score=10, date=date(2026, 7, 10)),

    Grade(student_id=mohammad.id, subject="ریاضی", score=18, date=date(2026, 6, 1)),
    Grade(student_id=mohammad.id, subject="علوم", score=17, date=date(2026, 7, 5)),

    Grade(student_id=maryam.id, subject="ادبیات", score=14, date=date(2026, 6, 1)),
    Grade(student_id=maryam.id, subject="ادبیات", score=12, date=date(2026, 7, 1)),
])

# ===== قدم ۵: حضور و غیاب — علی ۳ غیبت، سارا ۲ غیبت (آستانه‌ی غیرعادی: ۲) =====
db.add_all([
    Attendance(student_id=ali.id, date=date(2026, 8, 1), status="present"),
    Attendance(student_id=ali.id, date=date(2026, 8, 2), status="absent"),
    Attendance(student_id=ali.id, date=date(2026, 8, 3), status="present"),
    Attendance(student_id=ali.id, date=date(2026, 8, 5), status="absent"),
    Attendance(student_id=ali.id, date=date(2026, 8, 6), status="absent"),

    Attendance(student_id=sara.id, date=date(2026, 8, 1), status="absent"),
    Attendance(student_id=sara.id, date=date(2026, 8, 2), status="absent"),
    Attendance(student_id=sara.id, date=date(2026, 8, 3), status="present"),

    Attendance(student_id=mohammad.id, date=date(2026, 8, 1), status="present"),
    Attendance(student_id=mohammad.id, date=date(2026, 8, 2), status="present"),
    Attendance(student_id=maryam.id, date=date(2026, 8, 1), status="present"),
])

# ===== قدم ۶: برنامه امتحانات =====
db.add_all([
    Exam(subject="ریاضی", class_name="هشتم ۲", date=date(2026, 8, 20)),
    Exam(subject="علوم", class_name="هشتم ۲", date=date(2026, 8, 25)),
    Exam(subject="ریاضی", class_name="هشتم ۱", date=date(2026, 8, 22)),
])

# ===== قدم ۷: نمونه شهریه — یک قسط معوق برای تست اخطار =====
db.add_all([
    Tuition(student_id=ali.id, amount=2500000, due_date=date(2026, 7, 1), description="قسط اول", is_paid=True),
    Tuition(student_id=ali.id, amount=2500000, due_date=date(2026, 8, 1), description="قسط دوم", is_paid=False),
    Tuition(student_id=sara.id, amount=2500000, due_date=date(2026, 8, 1), description="قسط دوم", is_paid=False),
])

db.commit()
db.close()

print("✅ دیتابیس اولیه ساخته شد:")
print("   • ۴ دانش‌آموز — رمز والد همه: 1234")
print("   • معلم: teacher1 / 1234 (کلاس هشتم ۲)")
print("   • مدیر: admin / school1234")
print("   • ۱۱ نمره، ۱۱ حضور/غیاب، ۳ امتحان، ۳ قسط")