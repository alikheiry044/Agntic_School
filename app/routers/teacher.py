from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Teacher, Student, Grade, Attendance, Report
from app.schemas import (
    TeacherResponse,
    GradeCreate, GradeResponse,
    AttendanceCreate, AttendanceResponse,
    MonthlyReportCreate, ReportResponse
)

router = APIRouter(prefix="/teachers", tags=["Teachers"])


# ۱. لیست همه معلم‌ها (برای فرانت‌اند که بخواد معلم انتخاب کنه)
@router.get("/", response_model=List[TeacherResponse])
def get_all_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).all()


# ۲. دریافت لیست دانش‌آموزان کلاسِ این معلم
@router.get("/{teacher_id}/students", response_model=List[dict])
def get_class_students(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="معلم یافت نشد")

    students = db.query(Student).filter(Student.class_name == teacher.class_name).all()
    return [{"id": s.id, "name": s.name, "class_name": s.class_name} for s in students]


# ۳. ثبت نمره توسط معلم (با بررسی هوشمند کلاس)
@router.post("/{teacher_id}/grades", response_model=GradeResponse, status_code=201)
def add_grade(teacher_id: int, grade_data: GradeCreate, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="معلم یافت نشد")

    student = db.query(Student).filter(Student.id == grade_data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="دانش‌آموز یافت نشد")

    if teacher.class_name != student.class_name:
        raise HTTPException(
            status_code=403,
            detail=f"شما مجاز به ثبت نمره برای کلاس {student.class_name} نیستید. کلاس شما: {teacher.class_name}"
        )

    new_grade = Grade(
        student_id=grade_data.student_id,
        subject=grade_data.subject,
        score=grade_data.score,
        date=grade_data.date
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade


# ۴. ثبت حضور و غیاب توسط معلم (با بررسی هوشمند کلاس)
@router.post("/{teacher_id}/attendances", response_model=AttendanceResponse, status_code=201)
def add_attendance(teacher_id: int, attendance_data: AttendanceCreate, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="معلم یافت نشد")

    student = db.query(Student).filter(Student.id == attendance_data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="دانش‌آموز یافت نشد")

    if teacher.class_name != student.class_name:
        raise HTTPException(
            status_code=403,
            detail=f"شما مجاز به ثبت غیبت برای کلاس {student.class_name} نیستید."
        )

    new_attendance = Attendance(
        student_id=attendance_data.student_id,
        date=attendance_data.date,
        status=attendance_data.status
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    return new_attendance


# ۵. ثبت گزارش ماهانه توسط معلم (میره پیش مدیر برای تأیید)
@router.post("/{teacher_id}/monthly-report", response_model=ReportResponse, status_code=201)
def create_monthly_report(teacher_id: int, report_data: MonthlyReportCreate, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="معلم یافت نشد")

    student = db.query(Student).filter(Student.id == report_data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="دانش‌آموز یافت نشد")

    if teacher.class_name != student.class_name:
        raise HTTPException(
            status_code=403,
            detail=f"شما مجاز به ثبت گزارش برای کلاس {student.class_name} نیستید."
        )

    # ساخت محتوای گزارش از ترکیب وضعیت تحصیلی و انضباطی
    content = f"گزارش ماه {report_data.month}\n\n"
    content += f"وضعیت تحصیلی: {report_data.academic_comment}\n\n"
    content += f"وضعیت انضباطی: {report_data.behavior_comment}"

    new_report = Report(
        student_id=report_data.student_id,
        content=content,
        status="pending"  # منتظر تأیید مدیر
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report
