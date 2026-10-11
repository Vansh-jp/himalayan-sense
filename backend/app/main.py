from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.workers.scheduler import shutdown_scheduler, start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("himalayasense")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables, upload dir, and start background workers
    logger.info("Initializing HimalayaSense Database schemas...")
    Base.metadata.create_all(bind=engine)

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Early-Warning & Citizen Reporting Platform for Landslides, Flash-Floods & Unsafe Roads in Uttarakhand",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
origins = list(settings.CORS_ORIGINS)
if settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local uploads folder for citizen photos
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def root_status():
    return {
        "app": settings.PROJECT_NAME,
        "status": "operational",
        "version": "1.0.0",
        "pilot_region": "Dehradun, Uttarakhand",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }
