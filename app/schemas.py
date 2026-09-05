from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ===== اسکیماهای دانش‌آموز =====
class StudentBase(BaseModel):
    name: str
    class_name: str
    parent_name: str


class StudentCreate(StudentBase):
    password: Optional[str] = "1234"


class StudentResponse(StudentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    class_name: Optional[str] = None
    parent_name: Optional[str] = None
# ===== اسکیماهای نمره =====
class GradeCreate(BaseModel):
    student_id: int
    subject: str
    score: float
    date: date


class GradeResponse(BaseModel):
    id: int
    subject: str
    score: float
    date: date

    model_config = ConfigDict(from_attributes=True)


# ===== اسکیماهای حضور و غیاب =====
class AttendanceCreate(BaseModel):
    student_id: int
    date: date
    status: str


class AttendanceResponse(BaseModel):
    id: int
    date: date
    status: str

    model_config = ConfigDict(from_attributes=True)


# ===== اسکیماهای امتحان =====
class ExamResponse(BaseModel):
    id: int
    subject: str
    class_name: str
    date: date

    model_config = ConfigDict(from_attributes=True)


# ===== اسکیماهای شهریه (جدید) =====
class TuitionCreate(BaseModel):
    student_id: int
    amount: float
    due_date: date
    description: Optional[str] = "قسط شهریه"


class TuitionResponse(BaseModel):
    id: int
    student_id: int
    amount: float
    due_date: date
    is_paid: bool
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TuitionUpdatePay(BaseModel):
    is_paid: bool = True


# ===== اسکیماهای گزارش =====
class ReportResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    content: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== اسکیماهای ورود و توکن =====
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    student_name: Optional[str] = None


class ParentLogin(BaseModel):
    student_id: int
    password: str


class AdminLogin(BaseModel):
    username: str
    password: str


class TeacherLogin(BaseModel):
    username: str
    password: str

class MonthlyReportCreate(BaseModel):
    student_id: int
    month: str             # مثلاً "مهر" یا "آبان"
    academic_comment: str  # وضعیت تحصیلی
    behavior_comment: str  # وضعیت انضباطی

# ===== اسکیماهای دبیر (جدید) =====
class TeacherCreate(BaseModel):
    name: str
    subject: str        # درس مربوطه (مثلا: ریاضی)
    class_name: str     # کلاسی که تدریس می‌کند
    username: str
    password: str

class TeacherResponse(BaseModel):
    id: int
    name: str
    subject: str
    class_name: str
    username: str

    model_config = ConfigDict(from_attributes=True)



class ParentMeetingSMS(BaseModel):
    class_name: Optional[str] = None  # اگر None باشد برای کل مدرسه ارسال می‌شود
    meeting_date: str                 # مثلا: "چهارشنبه ۱۵ مهر ساعت ۱۶"
    agenda: Optional[str] = "بررسی وضعیت تحصیلی و انضباطی"  # دستور جلسه