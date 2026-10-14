import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
# from app.services.telegram_service import ...
# from sqlalchemy.orm import Session
# from app.routers.database import ...
# from .database import get_db
# from .models import Student, Teacher
# from .schemas import ParentLogin, AdminLogin, TeacherLogin, Token
from app.database import get_db
from app.models import Student, Teacher
from app.schemas import ParentLogin, AdminLogin, TeacherLogin, Token
SECRET_KEY = os.getenv("SECRET_KEY", "school-ai-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="ورود الزامی است")

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="نشست شما منقضی شده، دوباره وارد شوید")

    return payload


def require_parent(user: dict = Depends(get_current_user)):
    if user.get("role") != "parent":
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    return user


def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    return user


def require_admin_or_teacher(user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "teacher"):
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    return user


def require_owner_or_admin(student_id: int, user: dict = Depends(get_current_user)):
    """
    اجازه دسترسی می‌ده اگه:
    - کاربر ادمین باشه، یا
    - کاربر والدی باشه که فقط به فرزند خودش (همون student_id توی مسیر) دسترسی داره.
    """
    if user.get("role") == "admin":
        return user
    if user.get("role") == "parent" and user.get("student_id") == student_id:
        return user
    raise HTTPException(status_code=403, detail="شما فقط به اطلاعات فرزند خودتان دسترسی دارید")


# ==========================================
# روتر ورود (این چیزیه که تا الان اصلاً وجود نداشت —
# main.py دنبال app.auth.router می‌گرده ولی هیچ‌وقت تعریف نشده بود)
# ==========================================

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/parent/login", response_model=Token)
def parent_login(data: ParentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student or not student.hashed_password:
        raise HTTPException(status_code=401, detail="دانش‌آموز یا رمز عبور نادرست است")
    if not verify_password(data.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="دانش‌آموز یا رمز عبور نادرست است")

    token = create_access_token({"role": "parent", "student_id": student.id})
    return {"access_token": token, "role": "parent", "student_name": student.name}


@router.post("/teacher/login", response_model=Token)
def teacher_login(data: TeacherLogin, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.username == data.username).first()
    if not teacher or not verify_password(data.password, teacher.hashed_password):
        raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور نادرست است")

    token = create_access_token({"role": "teacher", "teacher_id": teacher.id})
    return {"access_token": token, "role": "teacher"}


@router.post("/admin/login", response_model=Token)
def admin_login(data: AdminLogin):
    if data.username != ADMIN_USERNAME or data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور نادرست است")

    token = create_access_token({"role": "admin"})
    return {"access_token": token, "role": "admin"}