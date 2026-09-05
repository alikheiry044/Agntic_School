from datetime import date
from app.database import Base, engine, SessionLocal
from app.models import Student, Grade, Attendance, Exam

# قدم ۱: ساخت واقعی جدول‌ها در دیتابیس
Base.metadata.create_all(bind=engine)

# قدم ۲: باز کردن یک Session برای کار با دیتابیس
db = SessionLocal()

# قدم ۳: ساخت یک دانش‌آموز نمونه
ali = Student(
    name="علی رضایی",
    class_name="هشتم ۲",
    parent_name="مریم رضایی"
)
db.add(ali)
db.commit()
db.refresh(ali)  # حالا ali.id مقدار واقعی گرفته

# قدم ۴: ثبت چند نمره برای علی
grades = [
    Grade(student_id=ali.id, subject="ریاضی", score=15, date=date(2026, 6, 1)),
    Grade(student_id=ali.id, subject="ریاضی", score=17, date=date(2026, 7, 1)),
    Grade(student_id=ali.id, subject="علوم", score=12, date=date(2026, 7, 5)),
]
db.add_all(grades)

# قدم ۵: ثبت چند رکورد حضور و غیاب
attendances = [
    Attendance(student_id=ali.id, date=date(2026, 8, 1), status="present"),
    Attendance(student_id=ali.id, date=date(2026, 8, 2), status="absent"),
    Attendance(student_id=ali.id, date=date(2026, 8, 3), status="present"),
]
db.add_all(attendances)

# قدم ۶: ثبت یک امتحان نمونه
exam = Exam(subject="ریاضی", class_name="هشتم ۲", date=date(2026, 8, 20))
db.add(exam)

# قدم ۷: ذخیره نهایی همه چیز
db.commit()
db.close()

print("✅ داده‌های نمونه با موفقیت ثبت شدند.")