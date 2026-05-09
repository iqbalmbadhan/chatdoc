# pyrefly: ignore [missing-import]
import structlog
from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import create_tables
from app.core.redis import init_redis, close_redis
from app.api.routes import (
    auth, chat, documents, providers, analytics,
    visitors, logs, system, keys,
)
from app.api.routes import settings as settings_router
from app.websocket.router import ws_router

logger = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ChatDoc", environment=settings.ENVIRONMENT)
    await init_redis()
    await create_tables()
    yield
    await close_redis()
    logger.info("ChatDoc stopped")


app = FastAPI(
    title="ChatDoc API",
    description="AI Document Chatbot Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
    except Exception as exc:
        logger.error("Middleware error", path=request.url.path, error=str(exc), exc_info=True)
        detail = str(exc) if settings.DEBUG else "An internal error occurred in middleware."
        return JSONResponse(
            status_code=500,
            content={"detail": detail},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if settings.DEBUG else "An internal error occurred."},
    )


# ─── Static files ─────────────────────────────────────────────────────────────
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# ─── REST Routers ─────────────────────────────────────────────────────────────
app.include_router(auth.router,            prefix="/auth",      tags=["Auth"])
app.include_router(documents.router,       prefix="/documents", tags=["Documents"])
app.include_router(chat.router,            prefix="/chat",      tags=["Chat"])
app.include_router(providers.router,       prefix="/providers", tags=["Providers"])
app.include_router(analytics.router,       prefix="/analytics", tags=["Analytics"])
app.include_router(visitors.router,        prefix="/visitors",  tags=["Visitors"])
app.include_router(logs.router,            prefix="/logs",      tags=["Logs"])
app.include_router(system.router,          prefix="/system",    tags=["System"])
app.include_router(settings_router.router, prefix="/settings",  tags=["Settings"])
app.include_router(keys.router,            prefix="/keys",      tags=["Keys"])

# ─── WebSocket ────────────────────────────────────────────────────────────────
app.include_router(ws_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
