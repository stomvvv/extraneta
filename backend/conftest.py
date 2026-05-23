"""
Top-level conftest: set required env vars before any app module is imported.
This allows unit tests to run without a real database or Redis.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters!!")
os.environ.setdefault("ENVIRONMENT", "test")
