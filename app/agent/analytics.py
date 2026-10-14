"""تحلیل‌های پیشرفت — میانگین نمرات ماه‌به‌ماه و غیبت‌ها."""

from datetime import date
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models import Grade, Attendance, Student, Tuition
from app.database import get_db
from .models import Grade, Attendance, Student, Tuition
from .auth import require_admin_or_teacher

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ==========================================
# توابع منطقی و محاسباتی (Logic Functions)
# ==========================================

def check_grade_drop(db: Session, student_id: int) -> List[Dict[str, Any]]:
    """نمرات هر درس را بر اساس تاریخ مرتب کرده و افت نمره را گزارش می‌کند."""
    grades = (
        db.query(Grade)
        .filter(Grade.student_id == student_id)
        .order_by(Grade.subject, Grade.date)
        .all()
    )

    subjects = {}
    for g in grades:
        subjects.setdefault(g.subject, []).append(g)

    report = []
    for subject, records in subjects.items():
        if len(records) < 2:
            continue
        last = records[-1]
        previous = records[-2]
        diff = last.score - previous.score
        if diff < 0:
            report.append({
                "subject": subject,
                "previous_score": previous.score,
                "last_score": last.score,
                "change": round(diff, 2),
                "status": "افت"
            })
        else:
            report.append({
                "subject": subject,
                "previous_score": previous.score,
                "last_score": last.score,
                "change": round(diff, 2),
                "status": "پیشرفت" if diff > 0 else "ثابت"
            })

    return report


def check_unusual_absence(db: Session, student_id: int, threshold: int = 2) -> Dict[str, Any]:
    """تعداد غیبت‌های غیرعادی دانش‌آموز را مشخص می‌کند."""
    absences = (
        db.query(Attendance)
        .filter(Attendance.student_id == student_id, Attendance.status == "absent")
        .all()
    )

    return {
        "total_absences": len(absences),
        "is_unusual": len(absences) >= threshold,
        "dates": [a.date for a in absences],
    }


def check_tuition_overdue(db: Session) -> List[Dict[str, Any]]:
    """اقساط/شهریه‌های عقب‌افتاده کل مدرسه را استخراج می‌کند."""
    today = date.today()

    overdue_records = (
        db.query(Tuition)
        .options(joinedload(Tuition.student))
        .filter(Tuition.due_date < today, Tuition.is_paid == False)
        .all()
    )

    reports = []
    for record in overdue_records:
        if record.student:
            desc = record.description or "شهریه"
            msg = (
                f"⚠️ **اخطار شهریه**: سررسید واریز شهریه دانش‌آموز {record.student.name} "
                f"مربوط به «{desc}» در تاریخ {record.due_date} گذشته است "
                f"و مبلغ {record.amount:,.0f} تومان هنوز پرداخت نشده است."
            )
            reports.append({
                "student_id": record.student.id,
                "student_name": record.student.name,
                "type": "tuition_warning",
                "content": msg
            })

    return reports


def get_school_wide_report(db: Session) -> List[Dict[str, Any]]:
    """گزارش کلی سطح مدرسه از دانش‌آموزان دارای مشکل افت یا غیبت."""
    students = db.query(Student).all()

    report = []
    for student in students:
        grades_report = check_grade_drop(db, student.id)
        attendance_report = check_unusual_absence(db, student.id)

        drops = [g for g in grades_report if g["status"] == "افت"]

        if drops or attendance_report["is_unusual"]:
            report.append({
                "student_id": student.id,
                "name": student.name,
                "class_name": student.class_name,
                "grade_drops": drops,
                "unusual_absence": attendance_report["is_unusual"],
                "total_absences": attendance_report["total_absences"],
            })

    return report


# ==========================================
# اندپوینت‌های FastAPI (Endpoints)
# ==========================================

@router.get("/progress/{student_id}")
def student_progress(
    student_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin_or_teacher)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="دانش‌آموز پیدا نشد")

    # میانگین نمرات هر ماه (مخصوص SQLite)
    month_expr = func.strftime("%Y-%m", Grade.date)
    grade_rows = (
        db.query(
            month_expr.label("month"),
            func.avg(Grade.score).label("avg_score"),
            func.count(Grade.id).label("grade_count"),
        )
        .filter(Grade.student_id == student_id)
        .group_by(month_expr)
        .order_by(month_expr)
        .all()
    )

    # تعداد غیبت هر ماه
    att_month_expr = func.strftime("%Y-%m", Attendance.date)
    absent_rows = (
        db.query(
            att_month_expr.label("month"),
            func.count(Attendance.id).label("absent_count"),
        )
        .filter(Attendance.student_id == student_id, Attendance.status == "absent")
        .group_by(att_month_expr)
        .order_by(att_month_expr)
        .all()
    )

    months = [r.month for r in grade_rows]
    averages = [round(float(r.avg_score), 2) for r in grade_rows]
    grade_counts = [r.grade_count for r in grade_rows]

    absent_map = {r.month: r.absent_count for r in absent_rows}
    absences = [absent_map.get(m, 0) for m in months]

    # تحلیل روند تغییرات
    trend = "flat"
    if len(averages) >= 2:
        diff = averages[-1] - averages[0]
        if diff > 0.5:
            trend = "up"
        elif diff < -0.5:
            trend = "down"

    overall_avg = round(sum(averages) / len(averages), 2) if averages else None
    total_absences = sum(absences)

    total_grades = db.query(func.count(Grade.id)).filter(Grade.student_id == student_id).scalar() or 0

    return {
        "student_id": student.id,
        "student_name": student.name,
        "class_name": student.class_name,
        "months": months,
        "averages": averages,
        "grade_counts": grade_counts,
        "absences": absences,
        "overall_avg": overall_avg,
        "total_absences": total_absences,
        "total_grades": total_grades,
        "trend": trend,
    }
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Grade, Attendance, Student
from app.database import get_db
from app.routers.auth import require_admin_or_teacher

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/progress/{student_id}")
def student_progress(
    student_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin_or_teacher)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="دانش‌آموز پیدا نشد")

    month_expr = func.strftime("%Y-%m", Grade.date)
    grade_rows = (
        db.query(
            month_expr.label("month"),
            func.avg(Grade.score).label("avg_score"),
            func.count(Grade.id).label("grade_count"),
        )
        .filter(Grade.student_id == student_id)
        .group_by(month_expr)
        .order_by(month_expr)
        .all()
    )

    att_month_expr = func.strftime("%Y-%m", Attendance.date)
    absent_rows = (
        db.query(
            att_month_expr.label("month"),
            func.count(Attendance.id).label("absent_count"),
        )
        .filter(Attendance.student_id == student_id, Attendance.status == "absent")
        .group_by(att_month_expr)
        .order_by(att_month_expr)
        .all()
    )

    months = [r.month for r in grade_rows]
    averages = [round(float(r.avg_score), 2) for r in grade_rows]
    grade_counts = [r.grade_count for r in grade_rows]

    absent_map = {r.month: r.absent_count for r in absent_rows}
    absences = [absent_map.get(m, 0) for m in months]

    trend = "flat"
    if len(averages) >= 2:
        diff = averages[-1] - averages[0]
        if diff > 0.5:
            trend = "up"
        elif diff < -0.5:
            trend = "down"

    overall_avg = round(sum(averages) / len(averages), 2) if averages else None
    total_absences = sum(absences)
    total_grades = db.query(func.count(Grade.id)).filter(Grade.student_id == student_id).scalar() or 0

    return {
        "student_id": student.id,
        "student_name": student.name,
        "class_name": student.class_name,
        "months": months,
        "averages": averages,
        "grade_counts": grade_counts,
        "absences": absences,
        "overall_avg": overall_avg,
        "total_absences": total_absences,
        "total_grades": total_grades,
        "trend": trend,
    }