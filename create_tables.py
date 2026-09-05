from app.database import Base, engine
from app.models import Student, Grade, Attendance, Exam, Report, Teacher, Tuition

Base.metadata.create_all(bind=engine)
print("✅ همه جدول‌ها (از جمله teachers و tuitions) بررسی و ساخته شدند.")