from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from dotenv import load_dotenv
from typing import Generator
from backend.config import settings

load_dotenv()

# Single source of truth for the connection string: settings.sqlalchemy_url
# prefers DATABASE_URL (managed hosts) and otherwise builds it from the
# discrete DB_* vars. Kept module-level because alembic/env.py and the test
# suite both import this name.
DATABASE_URL = settings.sqlalchemy_url

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

