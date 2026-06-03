import subprocess
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class GitManager:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_cmd(self, cmd: list) -> Tuple[bool, str]:
        """Runs a shell command and returns (success, output)."""
        try:
            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True, check=True)
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() or e.stdout.strip()
            logger.error(f"Git command failed: {' '.join(cmd)}\nError: {error_msg}")
            return False, error_msg

    def get_current_branch(self) -> str:
        success, output = self._run_cmd(["git", "branch", "--show-current"])
        return output if success else "unknown"

    def create_upgrade_branch(self, branch_name: str) -> bool:
        """Layer 13.2: Clone Creator Function - Creates isolated sandbox branch."""
        current_branch = self.get_current_branch()
        if current_branch != "master" and current_branch != "main":
            logger.warning(f"Creating upgrade branch from non-main branch: {current_branch}")
            
        success, _ = self._run_cmd(["git", "checkout", "-b", branch_name])
        if success:
            logger.info(f"Sandbox created: {branch_name}")
        return success

    def commit_changes(self, message: str) -> bool:
        """Commits atomic code changes made by the AI."""
        self._run_cmd(["git", "add", "."])
        success, _ = self._run_cmd(["git", "commit", "-m", message])
        return success

    def discard_upgrade(self) -> bool:
        """Layer 16.3 / 18.3: Emergency Rollback / Rejection Handler."""
        # Force checkout main and delete the sandbox branch
        self._run_cmd(["git", "checkout", "master"])
        # We don't delete immediately here just in case, but normally we would clean up
        return True
        
    def merge_upgrade(self, branch_name: str) -> bool:
        """Layer 16.2: Approval Gate passed - merge to main."""
        self._run_cmd(["git", "checkout", "master"])
        success, output = self._run_cmd(["git", "merge", branch_name, "--no-ff", "-m", f"Approved upgrade: {branch_name}"])
        if success:
            logger.info(f"Successfully merged {branch_name} into master.")
            return True
        else:
            logger.error(f"Merge conflict or error: {output}")
            self._run_cmd(["git", "merge", "--abort"]) # Auto rollback on conflict
            return False

git_manager = GitManager()
