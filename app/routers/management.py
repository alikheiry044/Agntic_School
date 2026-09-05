import io
import openpyxl
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, Grade, Attendance, Tuition, Teacher
from ..schemas import (
    StudentCreate,
    StudentUpdate,
    GradeCreate,
    AttendanceCreate,
    TuitionCreate,
    TuitionResponse,
    TeacherCreate,
    TeacherResponse,
)
from ..auth import require_admin, hash_password, require_admin_or_teacher

router = APIRouter(prefix="/manage", tags=["Management"])


# ===== مدیریت دبیران =====

@router.post("/teachers", response_model=TeacherResponse)
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    existing = db.query(Teacher).filter(Teacher.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="دبیری با این نام کاربری قبلاً ثبت شده است.")

    teacher = Teacher(
        name=data.name,
        subject=data.subject,
        class_name=data.class_name,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.get("/teachers", response_model=list[TeacherResponse])
def list_teachers(db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    return db.query(Teacher).all()


@router.delete("/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="دبیر پیدا نشد")
    db.delete(teacher)
    db.commit()
    return {"message": f"حساب کاربری دبیر «{teacher.name}» با موفقیت حذف شد."}


# ===== دانش‌آموزان =====

@router.post("/students")
def create_student(data: StudentCreate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    student = Student(
        name=data.name,
        class_name=data.class_name,
        parent_name=data.parent_name,
        hashed_password=hash_password(data.password),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"id": student.id, "name": student.name, "class_name": student.class_name}


@router.get("/students")
# def list_students(db: Session = Depends(get_db), user: dict = Depends(require_admin)):
# #     students = db.query(Student).all()
# #     return [
# #         {"id": s.id, "name": s.name, "class_name": s.class_name, "parent_name": s.parent_name}
# #         for s in students
# #     ]
@router.get("/students")
def list_students(db: Session = Depends(get_db), user: dict = Depends(require_admin_or_teacher)):
    students = db.query(Student).all()
    return [
        {"id": s.id, "name": s.name, "class_name": s.class_name, "parent_name": s.parent_name}
        for s in students
    ]

@router.put("/students/{student_id}")
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db),
                   user: dict = Depends(require_admin)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="دانش‌آموز پیدا نشد")
    if data.name is not None:
        student.name = data.name
    if data.class_name is not None:
        student.class_name = data.class_name
    if data.parent_name is not None:
        student.parent_name = data.parent_name
    db.commit()
    return {"message": "بروزرسانی شد", "id": student.id}


@router.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="دانش‌آموز پیدا نشد")
    db.delete(student)
    db.commit()
    return {"message": "دانش‌آموز حذف شد"}


@router.post("/students/import")
async def import_students(file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    content = await file.read()
    workbook = openpyxl.load_workbook(io.BytesIO(content))
    sheet = workbook.active

    created = []
    errors = []

    for i, row in enumerate(sheet.iter_rows(min_row=1, values_only=True), start=1):
        if not row or not row[0]:
            continue
        if str(row[0]).strip().lower() in ("نام", "name"):
            continue
        try:
            name = str(row[0]).strip()
            class_name = str(row[1]).strip()
            parent_name = str(row[2]).strip()
            password = str(row[3]).strip() if len(row) > 3 and row[3] else "1234"

            student = Student(
                name=name,
                class_name=class_name,
                parent_name=parent_name,
                hashed_password=hash_password(password),
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            created.append({"row": i, "name": name})
        except Exception as e:
            db.rollback()
            errors.append({"row": i, "error": str(e)})

    return {"created": created, "errors": errors, "total_created": len(created)}


# ===== نمرات =====

@router.post("/grades")
def create_grade(data: GradeCreate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    grade = Grade(student_id=data.student_id, subject=data.subject, score=data.score, date=data.date)
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return {"id": grade.id, "subject": grade.subject, "score": grade.score}


# ===== حضور و غیاب =====

@router.post("/attendance")
def create_attendance(data: AttendanceCreate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    record = Attendance(student_id=data.student_id, date=data.date, status=data.status)
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "status": record.status}


# ===== شهریه =====

@router.post("/tuition", response_model=TuitionResponse)
def add_tuition(data: TuitionCreate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="دانش‌آموز پیدا نشد")
    tuition = Tuition(**data.model_dump())
    db.add(tuition)
    db.commit()
    db.refresh(tuition)
    return tuition


@router.get("/tuition/student/{student_id}", response_model=list[TuitionResponse])
def get_student_tuitions(student_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    return db.query(Tuition).filter(Tuition.student_id == student_id).all()


@router.post("/tuition/{tuition_id}/pay")
def mark_tuition_paid(tuition_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    tuition = db.query(Tuition).filter(Tuition.id == tuition_id).first()
    if not tuition:
        raise HTTPException(status_code=404, detail="صورتحساب شهریه پیدا نشد")
    tuition.is_paid = True
    db.commit()
    return {"message": "وضعیت شهریه به پرداخت‌شده تغییر یافت.", "id": tuition_id}
