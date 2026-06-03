from google import genai
from google.genai import types
from app.core.config import Settings
from app.models.schemas import ChatRequest, ChatResponse
from app.memory.pinecone_db import memory_graph
from app.psychology.analyzer import psychology_analyzer
import os
import logging

logger = logging.getLogger(__name__)

# Always load fresh settings (bypass lru_cache)
_settings = Settings()

# Use latest available model
PRIMARY_MODEL   = "gemini-2.0-flash"
REASONING_MODEL = "gemini-2.0-flash"

# Initialize client
client = None
if _settings.gemini_api_key:
    client = genai.Client(api_key=_settings.gemini_api_key)
    logger.info(f"Gemini API (google.genai) initialized. Model: {PRIMARY_MODEL}")
else:
    logger.warning("Gemini API key not found. Orchestrator will fail.")

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
    Overwrites the desktop UI files (index.html, style.css, or renderer.js) with new content.
    Call this tool ONLY when the user explicitly asks you to change your visual design, UI, or appearance.
    """
    allowed_files = {"index.html", "style.css", "renderer.js"}
    if filename not in allowed_files:
        return f"Error: Cannot edit {filename}. Only allowed: {allowed_files}"
    
    filepath = os.path.join("d:\\ai-revolution\\desktop", filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(file_content)
        return f"Successfully updated {filename}. The UI will reload automatically."
    except Exception as e:
        return f"Error writing file: {e}"


class Orchestrator:
    def __init__(self):
        self.is_mock = False
        self.chat_sessions = {}  # session_id -> list of message dicts

    def _get_history(self, session_id: str):
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []
        return self.chat_sessions[session_id]

    async def process_request(self, request: ChatRequest) -> ChatResponse:
        """
        Layer 4: AI Core (Orchestrator)
        """
        logger.info(f"Processing request in Orchestrator. Session: {request.session_id}")
        
        session_id = request.session_id or "default_session"
        history = self._get_history(session_id)

        # 1. Psychology Analysis (Layer 3)
        psyche = psychology_analyzer.analyze_state(request.message)
        psyche_block = f"\n\n[USER PSYCHOLOGICAL STATE]\nMood: {psyche.get('mood')}\nStress Level: {psyche.get('stress_level')}\nPreferred Style: {psyche.get('style_preference')}"
        
        if psyche.get("stress_level") == "High":
            psyche_block += "\nWARNING: User is highly stressed. Simplify language, reduce cognitive load, and be highly supportive."

        # 2. Retrieve Memories (Layer 5.4)
        past_memories = memory_graph.retrieve_memories(request.message)
        memory_block = ""
        if past_memories:
            memory_block = f"\n\n[RETRIEVED MEMORIES]\n{past_memories}"

        enriched_prompt = f"{request.message}{psyche_block}{memory_block}"

        # 3. Build contents list with history
        contents = list(history)
        contents.append({"role": "user", "parts": [{"text": enriched_prompt}]})

        # 4. Dispatch to Gemini
        try:
            response = client.models.generate_content(
                model=PRIMARY_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=MASTER_SYSTEM_PROMPT,
                    temperature=0.7,
                )
            )
            reply_text = response.text

            # Update history
            history.append({"role": "user", "parts": [{"text": request.message}]})
            history.append({"role": "model", "parts": [{"text": reply_text}]})

            # 5. Store Memory (Layer 5.1)
            memory_graph.store_memory(f"User state: {psyche.get('mood')}. User said: {request.message} | AI replied: {reply_text}")

            trace = {
                "layer_3_psychology": psyche,
                "layer_4_orchestrator": "Dispatched to Gemini",
                "layer_5_memory_nodes_retrieved": bool(past_memories),
            }

            return ChatResponse(
                reply=reply_text,
                confidence_score=0.95,
                detected_mood=psyche.get("mood"),
                orchestration_trace=trace
            )
            
        except Exception as e:
            logger.error(f"Error calling API: {e}")
            return ChatResponse(
                reply="I encountered an error connecting to my core intelligence engine.",
                confidence_score=0.0,
                orchestration_trace={"error": str(e)}
            )

# Global instance
orchestrator = Orchestrator()
