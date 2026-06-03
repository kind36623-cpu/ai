import subprocess
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class Evaluator:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def run_tests(self) -> Tuple[bool, str]:
        """
        Layer 15: Evaluates the current branch by running pytest.
        Returns (success_boolean, output_string)
        """
        logger.info("Running test suite on sandbox branch...")
        try:
            # We run pytest and capture the output
            result = subprocess.run(
                ["pytest", "-v", "tests/"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            # returncode == 0 means all tests passed
            success = result.returncode == 0
            
            if success:
                logger.info("All tests passed. Upgrade candidate is stable.")
            else:
                logger.warning(f"Tests failed on sandbox branch.\n{result.stdout}\n{result.stderr}")
                
            return success, result.stdout
            
        except Exception as e:
            logger.error(f"Failed to execute pytest: {e}")
            return False, str(e)

evaluator = Evaluator()
