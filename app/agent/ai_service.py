"""سرویس چت هوشمند — پاسخ‌گویی به سؤالات مدیر از روی داده‌های واقعی دیتابیس.
بدون وابستگی به اینترنت؛ اگر در .env کلید LLM تعریف شود، آینده‌اً قابل اتصال است."""
from sqlalchemy.orm import Session
from app.models import Student, Report, Grade, Attendance


from sqlalchemy import func
from app.database import get_db, SessionLocal
from .analytics import get_school_wide_report, check_tuition_overdue
def _fmt_students_with_issues(db: Session) -> str:
    """متنی از دانش‌آموزان مشکل‌دار (افت یا غیبت غیرعادی)."""
    issues = get_school_wide_report(db)
    if not issues:
        return "در حال حاضر هیچ دانش‌آموزی افت تحصیلی یا غیبت غیرعادی ندارد. ✅"
    lines = [f"در مجموع {len(issues)} دانش‌آموز نیاز به بررسی دارند:"]
    for it in issues:
        parts = []
        for drop in it["grade_drops"]:
            parts.append(f"افت در {drop['subject']} (از {drop['previous_score']} به {drop['last_score']})")
        if it["unusual_absence"]:
            parts.append(f"{it['total_absences']} روز غیبت")
        lines.append(f"• {it['name']} ({it['class_name']}): " + "؛ ".join(parts))
    return "\n".join(lines)


def _fmt_tuition_overdue(db: Session) -> str:
    """متنی از اقساط معوق."""
    overdue = check_tuition_overdue(db)
    if not overdue:
        return "هیچ قسط معوقی وجود ندارد. ✅"
    lines = [f"در مجموع {len(overdue)} قسط عقب‌افتاده:"]
    for r in overdue:
        lines.append(f"• {r['student_name']}: {r['content']}")
    return "\n".join(lines)


def _fmt_attendance_month(db: Session) -> str:
    """خلاصه‌ی غیبت‌های کل مدرسه."""
    total = (
        db.query(Attendance)
        .filter(Attendance.status == "absent")
        .count()
    )
    return f"مجموع غیبت‌های ثبت‌شده در کل مدرسه: {total} روز.\nبرای جزئیات هر دانش‌آموز، تب «داشبورد پیشرفت» را ببین."


def _fmt_overall_stats(db: Session) -> str:
    """آمار کلی مدرسه."""
    students = db.query(Student).count()
    grades = db.query(Grade).count()
    avg = db.query(func.avg(Grade.score)).scalar()
    avg_txt = f"{round(float(avg), 2)} از ۲۰" if avg is not None else "هنوز نمره‌ای ثبت نشده"
    return (
        f"آمار کلی مدرسه:\n"
        f"• دانش‌آموزان: {students} نفر\n"
        f"• نمرات ثبت‌شده: {grades} مورد\n"
        f"• میانگین کل نمرات: {avg_txt}"
    )


def get_ai_answer(db: Session, question: str, role: str = "admin") -> str:
    """پاسخ به سؤال مدیر — بر اساس تشخیص موضوع از داده‌های واقعی."""
    q = question.strip().lower()

    if any(k in q for k in ("افت", "ضعیف", "کم شدن نمره", "تedral")):
        return _fmt_students_with_issues(db)

    if any(k in q for k in ("غیبت", "حضور", "absent")):
        # اگر پرسش «غیبت این ماه» بود هم خلاصه کل می‌دهیم + دانش‌آموزان پرغیبت
        return _fmt_attendance_month(db) + "\n\n" + _fmt_students_with_issues(db)

    if any(k in q for k in ("شهریه", "قسط", "پول", "پرداخت", "بدهی")):
        return _fmt_tuition_overdue(db)

    if any(k in q for k in ("میانگین", "وضعیت کلی", "آمار", "چند نفر", "دانش‌آموزان چطور")):
        return _fmt_overall_stats(db)

    if any(k in q for k in ("پیشرفت", "بهبود", "روند")):
        return _fmt_students_with_issues(db)

    # پاسخ پیش‌فرض — راهنما
    return (
        "من دستیار هوشمند مدرسه‌ام. می‌توانی این‌ها را بپرسی:\n"
        "• «کدام دانش‌آموزان افت تحصیلی داشته‌اند؟»\n"
        "• «وضعیت غیبت‌ها چطوره؟»\n"
        "• «اقساط معوق داریم؟»\n"
        "• «آمار کلی مدرسه»"
    )


