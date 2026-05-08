import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_tables
from app.core.redis import get_redis_client
from app.api.routes import auth, documents, chat, providers, analytics, visitors, logs, system, settings as settings_router, keys
from app.websocket.manager import ws_manager

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ChatDoc API", environment=settings.ENVIRONMENT)
    await create_tables()
    await ws_manager.startup()
    yield
    logger.info("Shutting down ChatDoc API")
    await ws_manager.shutdown()


app = FastAPI(
    title="ChatDoc API",
    description="AI Document Chatbot Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── Static files ─────────────────────────────────────────────────────────────
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router,       prefix="/auth",       tags=["Auth"])
app.include_router(documents.router,  prefix="/documents",  tags=["Documents"])
app.include_router(chat.router,       prefix="/chat",       tags=["Chat"])
app.include_router(providers.router,  prefix="/providers",  tags=["Providers"])
app.include_router(analytics.router,  prefix="/analytics",  tags=["Analytics"])
app.include_router(visitors.router,   prefix="/visitors",   tags=["Visitors"])
app.include_router(logs.router,       prefix="/logs",       tags=["Logs"])
app.include_router(system.router,     prefix="/system",     tags=["System"])
app.include_router(settings_router.router, prefix="/settings", tags=["Settings"])
app.include_router(keys.router,       prefix="/keys",       tags=["API Keys"])

# ─── WebSocket ────────────────────────────────────────────────────────────────
from app.websocket import handlers  # noqa: E402, F401


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
