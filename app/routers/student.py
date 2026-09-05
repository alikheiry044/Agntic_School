from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, Grade, Attendance, Exam
from ..analytics import check_grade_drop, check_unusual_absence
from ..agent.parent_agent import ask_parent_agent
from ..auth import require_parent

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="دانش‌آموز پیدا نشد")
    return {
        "id": student.id,
        "name": student.name,
        "class_name": student.class_name,
        "parent_name": student.parent_name,
    }


@router.get("/{student_id}/grades")
def get_student_grades(student_id: int, db: Session = Depends(get_db)):
    grades = db.query(Grade).filter(Grade.student_id == student_id).all()
    return [
        {"subject": g.subject, "score": g.score, "date": g.date}
        for g in grades
    ]


@router.get("/{student_id}/attendance")
def get_student_attendance(student_id: int, db: Session = Depends(get_db)):
    records = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    return [
        {"date": a.date, "status": a.status}
        for a in records
    ]


@router.get("/exams/{class_name}")
def get_exams(class_name: str, db: Session = Depends(get_db)):
    exams = db.query(Exam).filter(Exam.class_name == class_name).all()
    return [
        {"subject": e.subject, "date": e.date}
        for e in exams
    ]


@router.get("/{student_id}/analysis")
def get_student_analysis(student_id: int, db: Session = Depends(get_db)):
    return {
        "grades_report": check_grade_drop(db, student_id),
        "attendance_report": check_unusual_absence(db, student_id),
    }


@router.get("/{student_id}/ask")
def ask_about_student(
    student_id: int,
    question: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_parent),
):
    if user["student_id"] != student_id:
        raise HTTPException(status_code=403, detail="شما فقط به اطلاعات فرزند خودتان دسترسی دارید")

    answer = ask_parent_agent(db, student_id, question)
    return {"answer": answer}
