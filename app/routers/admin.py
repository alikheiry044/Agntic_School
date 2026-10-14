"""روت‌های مدیر — اسکن مدرسه، گزارش‌ها، تأیید/رد + تلگرام، چت هوشمند."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Report, Student
from app.schemas import ReportResponse
from app.routers.auth import require_admin
from app.agent.analytics import get_school_wide_report
from app.services.telegram_service import notify_parent, TelegramError
from app.services.ai_service import get_ai_answer
from sqlalchemy import func
from app.models import Student, Report, Tuition, Grade, Attendance
from app.agent.analytics import get_school_wide_report, check_grade_drop, check_unusual_absence


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/scan")
def scan_school(db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """
    مدرسه را برای افت نمره یا غیبت غیرعادی اسکن می‌کند و برای هر دانش‌آموزی
    که مشکل دارد (و گزارش pending قبلی ندارد)، یک گزارش تازه می‌سازد.
    """
    issues = get_school_wide_report(db)
    created = []

    for item in issues:
        existing = (
            db.query(Report)
            .filter(Report.student_id == item["student_id"], Report.status == "pending")
            .first()
        )
        if existing:
            continue

        lines = [f"دانش‌آموز {item['name']} (کلاس {item['class_name']}) نیاز به بررسی دارد:"]
        for drop in item["grade_drops"]:
            lines.append(
                f"- افت نمره در {drop['subject']}: از {drop['previous_score']} به {drop['last_score']}"
            )
        if item["unusual_absence"]:
            lines.append(f"- غیبت غیرعادی: مجموعاً {item['total_absences']} روز")

        report = Report(student_id=item["student_id"], content="\n".join(lines), status="pending")
        db.add(report)
        db.commit()
        db.refresh(report)
        created.append({"id": report.id, "student_name": item["name"], "content": report.content})

    return {"new_reports": created, "total_students_with_issues": len(issues)}


@router.get("/reports", response_model=List[ReportResponse])
def list_reports(status: str = "pending", db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    reports = db.query(Report).filter(Report.status == status).all()
    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "student_name": r.student.name if r.student else None,
            "content": r.content,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in reports
    ]


@router.post("/reports/{report_id}/approve")
def approve_report(report_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """تأیید گزارش → ارسال به والد (تلگرام خصوصی، با fallback گروهی)."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")

    report.status = "approved"
    db.commit()

    telegram_status = "skipped"
    if report.student:
        try:
            telegram_status = notify_parent(report.student, report.content)
        except TelegramError as e:
            telegram_status = f"failed: {e}"

    return {"message": "گزارش تأیید شد", "id": report.id, "telegram_status": telegram_status}


@router.post("/reports/{report_id}/reject")
def reject_report(report_id: int, status: str = None, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """رد گزارش."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    report.status = "rejected"
    db.commit()
    return {"message": "گزارش رد شد", "id": report.id}


@router.get("/ask")
def admin_ask(question: str, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """چت هوشمند مدیر — سؤال درباره کل مدرسه."""
    answer = get_ai_answer(db, question, role="admin")
    return {"answer": answer}