from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.storage import ensure_bucket_exists
from app.api.routes import auth, hotels, upload, bookings, analytics, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure MinIO bucket exists
    try:
        ensure_bucket_exists()
    except Exception as e:
        print(f"Warning: could not ensure storage bucket exists: {e}")
    yield
    # Shutdown: nothing needed


app = FastAPI(
    title="ExtranEta API",
    description="Financial analytics platform for hoteliers — OTA commission tracking",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes — all prefixed with /api
app.include_router(auth.router, prefix="/api")
app.include_router(hotels.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
