import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.imports import router as imports_router
from app.api.batches import router as batches_router
from app.api.records import router as records_router
from app.api.export import router as export_router
from app.api.stats import router as stats_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("leadqualify")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing LeadQualify AI database schema...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down LeadQualify AI.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise AI Website Qualification & Lead Filtering Platform",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(projects_router, prefix=f"{settings.API_V1_STR}/projects", tags=["Projects"])
app.include_router(imports_router, prefix=f"{settings.API_V1_STR}/imports", tags=["Imports"])
app.include_router(batches_router, prefix=f"{settings.API_V1_STR}/batches", tags=["Batches"])
app.include_router(records_router, prefix=f"{settings.API_V1_STR}/records", tags=["Records"])
app.include_router(export_router, prefix=f"{settings.API_V1_STR}/export", tags=["Export"])
app.include_router(stats_router, prefix=f"{settings.API_V1_STR}/stats", tags=["Statistics"])


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "model_configured": settings.OPENROUTER_MODEL,
        "openrouter_key_present": bool(settings.OPENROUTER_API_KEY),
    }


# Optional: Mount static frontend if exported for unified single-service hosting
import os
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
frontend_dist = os.path.join(root_dir, "frontend", "out")
if os.path.exists(frontend_dist) and os.path.isdir(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend_static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
