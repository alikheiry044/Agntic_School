import os
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from ..analytics import check_grade_drop, check_unusual_absence
from ..models import Student

load_dotenv()

client = OpenAI(
    api_key=os.getenv("METIS_API_KEY"),
    base_url=os.getenv("METIS_BASE_URL"),
)


def ask_parent_agent(db: Session, student_id: int, question: str) -> str:
    """
    اطلاعات دانش‌آموز رو از دیتابیس جمع می‌کنه و به مدل AI می‌ده
    تا یک جواب طبیعی و قابل‌فهم برای والد بسازه.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return "دانش‌آموزی با این مشخصات پیدا نشد."

    grades_report = check_grade_drop(db, student_id)
    attendance_report = check_unusual_absence(db, student_id)

    context = f"""
اطلاعات دانش‌آموز:
نام: {student.name}
کلاس: {student.class_name}

گزارش نمرات:
{grades_report}

گزارش غیبت:
{attendance_report}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "تو دستیار هوشمند مدرسه هستی و به والدین دانش‌آموزان "
                    "به زبان فارسی، ساده و دوستانه پاسخ می‌دی. فقط بر اساس "
                    "اطلاعاتی که بهت داده می‌شه جواب بده، چیزی رو از خودت نساز."
                ),
            },
            {
                "role": "user",
                "content": f"{context}\n\nسؤال والد: {question}",
            },
        ],
    )

    return response.choices[0].message.content