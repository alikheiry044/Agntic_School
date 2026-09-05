from datetime import date
from sqlalchemy.orm import Session, joinedload
from .models import Grade, Attendance, Student, Tuition


def check_grade_drop(db: Session, student_id: int):
    """
    نمرات هر درس را بر اساس تاریخ مرتب می‌کند و آخرین نمره را
    با نمره قبلی مقایسه می‌کند. در صورت افت نمره، گزارش ثبت می‌کند.
    """
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


def check_unusual_absence(db: Session, student_id: int, threshold: int = 2):
    """
    در صورتی که تعداد غیبت‌های دانش‌آموز از حد مجاز بیشتر باشد،
    به‌عنوان غیبت غیرعادی گزارش می‌شود.
    """
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


def check_tuition_overdue(db: Session):
    """
    بررسی اقساط/شهریه‌های عقب‌افتاده کل مدرسه و ثبت گزارش اخطار برای مدیر.
    """
    today = date.today()

    # دریافت اقساط معوقه به همراه اطلاعات دانش‌آموز در یک کوئری (بهینه‌سازی Join)
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


def get_school_wide_report(db: Session):
    """
    گزارش کلی سطح مدرسه: دانش‌آموزانی که افت تحصیلی یا غیبت غیرعادی دارند را مشخص می‌کند.
    """
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