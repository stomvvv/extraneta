from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base

# Import all models so Alembic/Base can see them
import models  # noqa: F401

from routers import hotels, dashboard, bookings, channels, upload, reports, anomalies, settings

app = FastAPI(
    title="ExtranEta API",
    description="Финансовая аналитика для отельеров — контроль OTA-комиссий",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    # Auto-create tables if they don't exist (SQLite dev mode)
    Base.metadata.create_all(bind=engine)


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}


app.include_router(hotels.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")
app.include_router(channels.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
