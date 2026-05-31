from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import settings

# Celery uses db+postgresql:// prefix; SQLAlchemy create_engine needs plain postgresql://
_db_url = settings.APP_DB_CONN or ""
if _db_url.startswith("db+"):
    _db_url = _db_url[3:]
engine = create_engine(_db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
