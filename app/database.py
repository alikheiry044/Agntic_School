"""اتصال دیتابیس — SQLite با پشتیبانی از session های FastAPI."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./school.db"

# check_same_thread=False برای کارکرد SQLite با FastAPI لازم است
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency برای تزریق session دیتابیس در endpoint ها."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()