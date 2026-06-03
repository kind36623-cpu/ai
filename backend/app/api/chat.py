from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ChatRequest, ChatResponse
from app.intelligence.orchestrator import orchestrator
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main endpoint for the Android app to communicate with the Seed AGI backend.
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")
        # Hand off to Layer 4 (Orchestrator)
        response = await orchestrator.process_request(request)
        return response
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during orchestration.")
