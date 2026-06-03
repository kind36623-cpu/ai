from app.core.config import settings
from groq import Groq
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PsychologyLayer:
    def __init__(self):
        self.is_enabled = bool(settings.groq_api_key)
        self.client = None
        if self.is_enabled:
            try:
                self.client = Groq(api_key=settings.groq_api_key)
                logger.info("Psychology Layer (Groq) initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq: {e}")
                self.is_enabled = False

    def analyze_state(self, message: str) -> Dict[str, Any]:
        """
        Layer 3: Combines Mood Detector, Communication Style Adapter, and Stress Detector.
        Uses a fast model to analyze the user's implicit state before the main reasoning happens.
        """
        if not self.is_enabled:
            return {"mood": "Unknown", "stress_level": "Unknown", "style_preference": "Standard"}

        prompt = f"""
        Analyze the following user message and output a JSON object describing their psychological state.
        We are looking for three things:
        1. "mood": Positive, Negative, or Neutral.
        2. "stress_level": Low, Medium, or High (look for short, choppy sentences, urgency, or frustration).
        3. "style_preference": "Short" (if they seem rushed), "Detailed" (if asking complex questions), or "Standard".

        User Message: "{message}"

        Output ONLY valid JSON. Format:
        {{
            "mood": "string",
            "stress_level": "string",
            "style_preference": "string"
        }}
        """

        try:
            # We use Llama 3 8B on Groq for ultra-fast, cheap processing
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a psychological analysis engine. Output only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result = completion.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Psychology analysis failed: {e}")
            return {"mood": "Unknown", "stress_level": "Unknown", "style_preference": "Standard", "error": str(e)}

# Global Instance
psychology_analyzer = PsychologyLayer()
