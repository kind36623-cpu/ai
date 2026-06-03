"""
Layer 16: Proposal Store — in-memory + file-backed registry of all upgrade proposals.
Persists to proposals.json so you don't lose pending upgrades across server restarts.
"""
import json
import os
import time
import logging
from typing import Dict, Optional
from app.models.schemas import UpgradeProposal, ProposalStatus

logger = logging.getLogger(__name__)

PROPOSALS_FILE = "proposals.json"

class ProposalStore:
    def __init__(self):
        self._store: Dict[str, UpgradeProposal] = {}
        self._load()

    # ── Persistence ───────────────────────────────────────────────

    def _load(self):
        if os.path.exists(PROPOSALS_FILE):
            try:
                with open(PROPOSALS_FILE, "r") as f:
                    data = json.load(f)
                    for pid, props in data.items():
                        self._store[pid] = UpgradeProposal(**props)
                logger.info(f"Loaded {len(self._store)} existing proposals.")
            except Exception as e:
                logger.warning(f"Could not load proposals.json: {e}")

    def _save(self):
        try:
            with open(PROPOSALS_FILE, "w") as f:
                json.dump(
                    {pid: p.model_dump() for pid, p in self._store.items()},
                    f, indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save proposals.json: {e}")

    # ── CRUD ──────────────────────────────────────────────────────

    def create(self, proposal: UpgradeProposal):
        self._store[proposal.proposal_id] = proposal
        self._save()

    def get(self, proposal_id: str) -> Optional[UpgradeProposal]:
        return self._store.get(proposal_id)

    def update_status(
        self,
        proposal_id: str,
        status: ProposalStatus,
        diff_preview: Optional[str] = None,
        test_output: Optional[str] = None
    ):
        p = self._store.get(proposal_id)
        if p:
            p.status = status
            p.updated_at = time.time()
            if diff_preview is not None:
                p.diff_preview = diff_preview
            if test_output is not None:
                p.test_output = test_output
            self._save()

    def list_awaiting(self):
        return [p for p in self._store.values() if p.status == ProposalStatus.AWAITING]

    def list_all(self):
        return list(self._store.values())


# Global instance
proposal_store = ProposalStore()
