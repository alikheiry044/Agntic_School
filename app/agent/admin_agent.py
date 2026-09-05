import os
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from ..analytics import get_school_wide_report

load_dotenv()

client = OpenAI(
    api_key=os.getenv("METIS_API_KEY"),
    base_url=os.getenv("METIS_BASE_URL"),
)


def ask_admin_agent(db: Session, question: str) -> str:
    """
    گزارش کلی مدرسه رو جمع می‌کنه و به مدل AI می‌ده تا
    یک پاسخ مدیریتی و قابل‌فهم برای مدیر مدرسه بسازه.
    """
    report = get_school_wide_report(db)

    context = f"""
گزارش کلی دانش‌آموزانی که افت تحصیلی یا غیبت غیرعادی دارند:
{report}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "تو دستیار هوشمند مدیریتی یک مدرسه هستی و به مدیر مدرسه "
                    "به زبان فارسی، ساده و حرفه‌ای پاسخ می‌دی. فقط بر اساس "
                    "اطلاعاتی که بهت داده می‌شه جواب بده، چیزی رو از خودت نساز. "
                    "اگه گزارش خالی بود، بگو در حال حاضر مشکلی گزارش نشده."
                ),
            },
            {
                "role": "user",
                "content": f"{context}\n\nسؤال مدیر: {question}",
            },
        ],
    )

    return response.choices[0].message.content


def generate_report_text(db: Session, student_name: str, class_name: str, drops, total_absences: int) -> str:
    """
    برای یک دانش‌آموز خاص که مشکل داره، یک متن گزارش کوتاه و
    آماده برای نمایش به والد می‌سازه.
    """
    context = f"""
دانش‌آموز: {student_name}
کلاس: {class_name}
افت نمرات: {drops}
تعداد غیبت: {total_absences}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "تو دستیار هوشمند مدرسه هستی. یک گزارش کوتاه (حداکثر ۳ جمله)، "
                    "مؤدبانه و به فارسی برای اطلاع‌رسانی به والد یک دانش‌آموز بساز "
                    "که در آن افت تحصیلی یا غیبت غیرعادی داشته. فقط بر اساس اطلاعاتی "
                    "که بهت داده می‌شه بنویس."
                ),
            },
            {"role": "user", "content": context},
        ],
    )

    return response.choices[0].message.content