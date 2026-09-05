from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    parent_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)

    # روابط با سایر جدول‌ها
    grades = relationship("Grade", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")
    tuitions = relationship("Tuition", back_populates="student")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

    student = relationship("Student", back_populates="grades")


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String, nullable=False)  # "present" یا "absent"

    student = relationship("Student", back_populates="attendances")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    date = Column(Date, nullable=False)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending / approved / rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class Tuition(Base):
    __tablename__ = "tuitions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    amount = Column(Float, nullable=False)        # مبلغ قسط/شهریه
    due_date = Column(Date, nullable=False)       # تاریخ سررسید (میلادی)
    is_paid = Column(Boolean, default=False)      # وضعیت پرداخت
    description = Column(String, nullable=True)   # مثلا: قسط اول / شهریه ثبت‌نام

    student = relationship("Student", back_populates="tuitions")

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)      # درس مربوطه (مثلاً ریاضی)
    class_name = Column(String, nullable=False)   # کلاسی که در آن تدریس می‌کند
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

