from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import require_teacher
from ..models import Grade, Attendance, Report
from ..schemas import GradeCreate, AttendanceCreate, MonthlyReportCreate

router = APIRouter(prefix="/teacher", tags=["Teacher Panel"])


@router.post("/grades")
def add_grade(data: GradeCreate, db: Session = Depends(get_db), user: dict = Depends(require_teacher)):
    grade = Grade(student_id=data.student_id, subject=data.subject, score=data.score, date=data.date)
    db.add(grade)
    db.commit()
    return {"message": "نمره با موفقیت توسط دبیر ثبت شد."}


@router.post("/attendance")
def add_attendance(data: AttendanceCreate, db: Session = Depends(get_db), user: dict = Depends(require_teacher)):
    record = Attendance(student_id=data.student_id, date=data.date, status=data.status)
    db.add(record)
    db.commit()
    return {"message": "وضعیت حضور/غیاب ثبت شد"}


@router.post("/monthly-report")
def create_monthly_report(data: MonthlyReportCreate, db: Session = Depends(get_db), user: dict = Depends(require_teacher)):
    content = f"📋 گزارش ماهانه ({data.month})\n\n🔹 وضعیت تحصیلی: {data.academic_comment}\n🔹 وضعیت انضباطی: {data.behavior_comment}"
    report = Report(student_id=data.student_id, content=content, status="pending")
    db.add(report)
    db.commit()
    return {"message": "گزارش ماهانه ثبت شد و در انتظار تأیید مدیر است."}