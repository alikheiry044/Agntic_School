from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import student, admin, auth, management, teacher

app = FastAPI()

app.include_router(auth.router)
app.include_router(student.router)
app.include_router(admin.router)
app.include_router(management.router)
app.include_router(teacher.router)

app.mount("/app", StaticFiles(directory="app/static", html=True), name="static")


@app.get("/")
def read_root():
    return {"message": "School AI is running"}