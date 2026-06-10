from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from backend.database import engine, get_db
from backend.routers import farms, auth, public
from backend.config import settings
from backend.rate_limit import limiter
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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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


@app.get("/healthz", tags=["ops"])
def healthz(response: Response, db: Session = Depends(get_db)):
    """Liveness + DB readiness probe. 503 when the database is unreachable
    so load balancers can pull the instance out of rotation."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Health check failed: database unreachable")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "down"}
    return {"status": "ok", "database": "up"}