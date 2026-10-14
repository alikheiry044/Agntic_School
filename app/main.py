import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
# from app.auth import router as auth_router
# from app.routers.auth import router as auth_router
# from app.admin import router as admin_router
# from app.teacher import router as teacher_router
# from app.student import router as student_router
# from app.analytics import router as analytics_router
# from app.manage import router as manage_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.student import router as student_router
from app.routers.teacher import router as teacher_router
from app.routers.manage import router as manage_router
#
# ۱. ایجاد نمونه اپلیکیشن FastAPI در ابتدا
app = FastAPI(
    title="School AI API",
    description="سامانه هوشمند مدیریت مدرسه",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ۲. ایجاد جداول دیتابیس
Base.metadata.create_all(bind=engine)

# ۳. مسیرهای باز کردن صفحات وب (HTML)
@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/admin-panel")
def read_admin():
    return FileResponse("static/admin.html")

@app.get("/teacher-panel")
def read_teacher():
    return FileResponse("static/teacher.html")

@app.get("/parent-panel")
def read_parent():
    return FileResponse("static/parent.html")

# ۴. ثبت تمامی روترهای بک‌اند پس از تعریف app
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(teacher_router)
app.include_router(student_router)
# app.include_router(analytics_router)
app.include_router(manage_router)