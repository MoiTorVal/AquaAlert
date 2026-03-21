from fastapi import FastAPI
from backend.database import engine, Base
from backend import models
from sqlalchemy import text
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print("Database connection verified on startup")
    except Exception as e:
        print(f"Error connecting to the database on startup: {e}")
    yield

app = FastAPI(lifespan=lifespan)