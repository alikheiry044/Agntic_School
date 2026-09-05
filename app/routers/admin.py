from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..auth import require_admin
from ..database import get_db
from ..agent.admin_agent import ask_admin_agent, generate_report_text
from ..analytics import get_school_wide_report
from ..models import Report


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..agent.admin_agent import ask_admin_agent, generate_report_text
from ..analytics import get_school_wide_report
from ..models import Report
from ..auth import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/ask")
def ask_admin(question: str, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    answer = ask_admin_agent(db, question)
    return {"answer": answer}


@router.post("/scan")
def scan_school(db: Session = Depends(get_db), user: dict = Depends(require_admin)):
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

        text = generate_report_text(
            db,
            student_name=item["name"],
            class_name=item["class_name"],
            drops=item["grade_drops"],
            total_absences=item["total_absences"],
        )

        report = Report(student_id=item["student_id"], content=text, status="pending")
        db.add(report)
        db.commit()
        db.refresh(report)
        created.append({"id": report.id, "student_name": item["name"], "content": text})

    return {"new_reports": created, "total_students_with_issues": len(issues)}


@router.get("/reports")
def list_reports(status: str = "pending", db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    reports = db.query(Report).filter(Report.status == status).all()
    return [
        {
            "id": r.id,
            "student_name": r.student.name,
            "content": r.content,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in reports
    ]


@router.post("/reports/{report_id}/approve")
def approve_report(report_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    report.status = "approved"
    db.commit()
    return {"message": "گزارش تأیید شد", "id": report.id}


@router.post("/reports/{report_id}/reject")
def reject_report(report_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    report.status = "rejected"
    db.commit()
    return {"message": "گزارش رد شد", "id": report.id}