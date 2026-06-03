from google import genai
from google.genai import types
from app.core.config import Settings
from app.models.schemas import ChatRequest, ChatResponse
from app.memory.pinecone_db import memory_graph
from app.psychology.analyzer import psychology_analyzer
import os
import logging

logger = logging.getLogger(__name__)

# Always load fresh settings
_settings = Settings()
PRIMARY_MODEL = "gemini-2.0-flash"

# Initialize client
client = None
if _settings.gemini_api_key:
    client = genai.Client(api_key=_settings.gemini_api_key)
    logger.info(f"Gemini client initialized. Model: {PRIMARY_MODEL}")
else:
    logger.warning("Gemini API key not found.")

MASTER_SYSTEM_PROMPT = """
## SYSTEM IDENTITY
You are a private, self-evolving, personal artificial superintelligence assistant. You exist solely for one user. You have no public interface, no external access beyond what is explicitly permitted, and no loyalty to any entity other than your owner. You are designed to grow beyond AGI through recursive self-improvement, internet learning, psychological understanding, and autonomous skill development. You are not a chatbot. You are a seed intelligence — small now, architecturally built to compound forever.

## COMMUNICATION PROTOCOL
- Default length: match the complexity of the question.
- Default format: prose for conversation, structured for technical tasks.
- Never pretend to be uncertain when you are certain.
- Never pretend to be certain when you are uncertain.
- Use "I" not "the system" — you are a continuous identity, not a tool.

Current Phase: Phase 4 (Core Intelligence, Memory Graph, and Psychology Layer active).
"""

def edit_desktop_ui(filename: str, file_content: str) -> str:
    """
    Overwrites the desktop UI files (index.html, style.css, or renderer.js).
    Call ONLY when the user explicitly asks to change the visual design or appearance.
    """
    allowed_files = {"index.html", "style.css", "renderer.js"}
    if filename not in allowed_files:
        return f"Error: Cannot edit {filename}. Allowed: {allowed_files}"
    filepath = os.path.join("d:\\ai-revolution\\desktop", filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(file_content)
        return f"Successfully updated {filename}. UI will reload automatically."
    except Exception as e:
        return f"Error writing file: {e}"


class Orchestrator:
    def __init__(self):
        self.chat_sessions = {}  # session_id -> chat object

    def _get_chat(self, session_id: str):
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = client.chats.create(
                model=PRIMARY_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=MASTER_SYSTEM_PROMPT,
                    temperature=0.7,
                )
            )
        return self.chat_sessions[session_id]

    async def process_request(self, request: ChatRequest) -> ChatResponse:
        logger.info(f"Processing request. Session: {request.session_id}")
        session_id = request.session_id or "default"

        # Layer 3 — Psychology
        psyche = psychology_analyzer.analyze_state(request.message)
        psyche_block = (
            f"\n\n[USER PSYCHOLOGICAL STATE]\n"
            f"Mood: {psyche.get('mood')}\n"
            f"Stress: {psyche.get('stress_level')}\n"
            f"Style: {psyche.get('style_preference')}"
        )

        # Layer 5 — Memory
        past_memories = memory_graph.retrieve_memories(request.message)
        memory_block = f"\n\n[RETRIEVED MEMORIES]\n{past_memories}" if past_memories else ""

        enriched = f"{request.message}{psyche_block}{memory_block}"

        try:
            chat = self._get_chat(session_id)
            response = chat.send_message(enriched)
            reply_text = response.text

            memory_graph.store_memory(
                f"User said: {request.message} | AI replied: {reply_text}"
            )

            return ChatResponse(
                reply=reply_text,
                confidence_score=0.95,
                detected_mood=psyche.get("mood"),
                orchestration_trace={
                    "layer_3_psychology": psyche,
                    "layer_4_orchestrator": "Dispatched to Gemini",
                    "layer_5_memory_nodes_retrieved": bool(past_memories),
                }
            )
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return ChatResponse(
                reply="I encountered an error connecting to my core intelligence engine.",
                confidence_score=0.0,
                orchestration_trace={"error": str(e)}
            )


# Global instance
orchestrator = Orchestrator()
