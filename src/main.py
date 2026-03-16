"""
InventoryManagement FastAPI Application
"""

from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
from db.pool import create_pool, close_pool
from api.auth import router as auth_router
from api.dashboard import router as dashboard_router
from api.products import router as products_router
from api.warehouses import router as warehouses_router
from api.transactions import router as transactions_router
from api.users import router as users_router
from api.categories import router as categories_router
from urllib.parse import quote_plus

from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}
host = DB_CONFIG["host"]
port = DB_CONFIG["port"]
database = DB_CONFIG["database"]
user = DB_CONFIG["user"]
password = quote_plus(os.getenv("DB_PASSWORD"))

DSN = f"postgresql://{user}:{password}@{host}:{port}/{database}"
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - setup and teardown."""
    # Startup: Create database connection pool
    app.state.db_pool= await create_pool(dsn=DSN,
    min_size=2,
    max_size=10,
    ssl='require')
    try:
        yield
    finally:
        # Shutdown: Close database pool
        await close_pool(app.state.db_pool)


# Create FastAPI application
app = FastAPI(
    title="Inventory Management API",
    description="Multi-tenant inventory management system with authentication",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
# Get allowed origins from environment variable or use defaults
allowed_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS enabled for origins: {allowed_origins}")

# Register routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(products_router)
app.include_router(warehouses_router)
app.include_router(transactions_router)
app.include_router(users_router)
app.include_router(categories_router)


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {"status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
    )
