import google.generativeai as genai
from app.core.config import settings
import logging
import os
import glob
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CodeEditor:
    def __init__(self):
        self.is_enabled = bool(settings.gemini_api_key)
        if self.is_enabled:
            # We use the reasoning model (e.g. Gemini 1.5 Pro) for complex coding tasks
            self.model = genai.GenerativeModel(
                model_name=settings.reasoning_model,
                system_instruction="You are an expert Python engineer. Output ONLY valid Python code. Do not include markdown blocks or explanations. Just the raw code."
            )

    def _get_project_context(self) -> str:
        """Reads all critical Python files to build a context string."""
        context = ""
        # Search for .py files in app directory
        search_pattern = os.path.join("app", "**", "*.py")
        files = glob.glob(search_pattern, recursive=True)
        files.append("main.py")
        
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    context += f"\n\n--- FILE: {file_path} ---\n"
                    context += f.read()
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
        return context

    async def propose_upgrade(self, target_file: str, instruction: str) -> Optional[str]:
        """
        Layer 13.3 & 7.4: Analyzes the codebase and proposes an edit to a specific file.
        Returns the raw new code.
        """
        if not self.is_enabled:
            logger.error("Gemini API not configured for CodeEditor.")
            return None
            
        logger.info(f"Analyzing codebase to upgrade {target_file}...")
        project_context = self._get_project_context()
        
        prompt = f"""
        Here is the current state of the backend codebase:
        {project_context}
        
        Your task is to completely rewrite the file `{target_file}` based on this instruction:
        "{instruction}"
        
        Return the absolute entire content of `{target_file}` with your improvements. 
        DO NOT wrap it in ```python blocks. Return raw code only.
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            new_code = response.text.strip()
            # Safety cleanup if the model included markdown blocks despite instructions
            if new_code.startswith("```python"):
                new_code = new_code[9:]
            if new_code.startswith("```"):
                new_code = new_code[3:]
            if new_code.endswith("```"):
                new_code = new_code[:-3]
                
            return new_code.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate upgrade proposal: {e}")
            return None

    def apply_edit(self, target_file: str, new_code: str) -> bool:
        """Writes the proposed code to the disk."""
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_code)
            logger.info(f"Successfully applied edit to {target_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply edit to {target_file}: {e}")
            return False

code_editor = CodeEditor()
