from fastapi import APIRouter
from app.api.chat import router as chat_router
from app.api.evolution import router as evolution_router

router = APIRouter()

router.include_router(chat_router, tags=["Intelligence"])
router.include_router(evolution_router, prefix="/evolution", tags=["Self-Evolution"])
