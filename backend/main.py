from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine
from sqlalchemy import text
from contextlib import asynccontextmanager
from backend.routers import farms, auth, public
from backend.config import settings
from backend.services.scheduler import start_scheduler, shutdown_scheduler
import logging



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Database connection verified on startup")
    except Exception as e:
        logger.error(f"Error connecting to the database on startup: {e}")
    if settings.scheduler_enabled:
        start_scheduler()
    yield
    if settings.scheduler_enabled:
        shutdown_scheduler()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(farms.router, prefix="/farms", tags=["farms"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(public.router, tags=["public"])