import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
# from ..models import Student
from ..models import Student, Teacher
from ..auth import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")


class ParentLoginRequest(BaseModel):
    student_id: int
    password: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str

class TeacherLoginRequest(BaseModel):
    username: str
    password: str



@router.post("/parent/login")
def parent_login(data: ParentLoginRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student or not student.hashed_password:
        raise HTTPException(status_code=401, detail="دانش‌آموز یا رمز عبور نادرست است")

    if not verify_password(data.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="دانش‌آموز یا رمز عبور نادرست است")

    token = create_access_token({"role": "parent", "student_id": student.id})
    return {"access_token": token, "student_name": student.name}


@router.post("/admin/login")
def admin_login(data: AdminLoginRequest):
    if data.username != ADMIN_USERNAME or data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور نادرست است")

    token = create_access_token({"role": "admin"})

    return {"access_token": token}

@router.post("/teacher/login")
def teacher_login(data: TeacherLoginRequest, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.username == data.username).first()
    if not teacher or not verify_password(data.password, teacher.hashed_password):
        raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور نادرست است")

    token = create_access_token({
        "role": "teacher",
        "teacher_id": teacher.id,
        "subject": teacher.subject,
        "class_name": teacher.class_name,
    })
    return {
        "access_token": token,
        "teacher_name": teacher.name,
        "subject": teacher.subject,
        "class_name": teacher.class_name,
    }
