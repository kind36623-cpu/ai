from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
import time

class SensorContext(BaseModel):
    battery_level: Optional[int] = None
    is_charging: Optional[bool] = None
    activity: Optional[str] = None  # e.g., "still", "walking", "driving"
    location_zone: Optional[str] = None # e.g., "home", "work"
    time_of_day: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    is_voice: bool = False
    context: Optional[SensorContext] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    confidence_score: float = 1.0
    detected_mood: Optional[str] = None
    orchestration_trace: Optional[Dict[str, Any]] = None

# ── Evolution Schemas ────────────────────────────────────────────────

class ProposalStatus(str, Enum):
    PENDING   = "PENDING"    # Running in background
    TESTING   = "TESTING"    # pytest running in sandbox
    AWAITING  = "AWAITING"   # Tests passed, waiting for your approval
    APPROVED  = "APPROVED"   # Merged to master
    REJECTED  = "REJECTED"   # Discarded by user
    FAILED    = "FAILED"     # Tests failed, auto-discarded

class UpgradeProposalRequest(BaseModel):
    instruction: str
    target_file: str

class UpgradeProposal(BaseModel):
    proposal_id: str
    instruction: str
    target_file: str
    branch_name: str
    status: ProposalStatus
    diff_preview: Optional[str] = None   # what the AI changed
    test_output: Optional[str] = None    # pytest results
    created_at: float = 0.0
    updated_at: float = 0.0
