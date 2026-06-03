from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import router as api_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time
import logging

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ── FastAPI app ───────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Seed Intelligence AGI Backend — 19-Layer Architecture",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ── CORS — allow Android app to connect ──────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request timing middleware ─────────────────────────────────────────────
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    logger.info(f"{request.method} {request.url.path} → {elapsed*1000:.1f}ms")
    return response

# ── Routes ────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")

# ── Startup / shutdown ────────────────────────────────────────────────────
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def on_startup():
    logger.info("══════════════════════════════════════════")
    logger.info(f"  {settings.app_name} v{settings.app_version} — Starting up")
    logger.info("══════════════════════════════════════════")

    # Layer 6: Schedule Internet Learning Cycle every 6 hours
    if settings.crawler_enabled:
        from app.world_model.crawler import crawler
        scheduler.add_job(
            crawler.crawl_and_learn,
            trigger="interval",
            hours=settings.crawler_schedule_hours,
            id="internet_learning",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"Layer 6 — Internet crawler scheduled every {settings.crawler_schedule_hours}h")
    else:
        logger.info("Layer 6 — Internet crawler DISABLED (set CRAWLER_ENABLED=true to enable)")

    # Log which layers are live
    logger.info(f"Layer 3  — Psychology Analyzer : {'ONLINE' if settings.groq_api_key else 'OFFLINE'}")
    logger.info(f"Layer 4  — Orchestrator        : {'ONLINE' if settings.gemini_api_key else 'OFFLINE'}")
    logger.info(f"Layer 5  — Memory Graph        : {'ONLINE' if settings.pinecone_api_key else 'OFFLINE'}")
    logger.info(f"Layer 13 — Self-Evolution      : ONLINE")
    logger.info("══════════════════════════════════════════")

@app.on_event("shutdown")
async def on_shutdown():
    if scheduler.running:
        scheduler.shutdown()
    logger.info(f"{settings.app_name} shut down cleanly.")

# ── Health check ──────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "status"  : "online",
        "app"     : settings.app_name,
        "version" : settings.app_version,
        "layers"  : {
            "psychology" : bool(settings.groq_api_key),
            "intelligence": bool(settings.gemini_api_key),
            "memory"     : bool(settings.pinecone_api_key),
            "evolution"  : True,
            "crawler"    : settings.crawler_enabled,
        }
    }

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}

# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
