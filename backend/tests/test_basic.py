"""
Tests for Layer 4 — Orchestrator schema validation
"""
import pytest
from app.models.schemas import (
    ChatRequest, ChatResponse, SensorContext,
    UpgradeProposal, ProposalStatus
)
import time


class TestChatSchemas:
    def test_chat_request_minimal(self):
        req = ChatRequest(message="Hello")
        assert req.message == "Hello"
        assert req.is_voice is False
        assert req.context is None
        assert req.session_id is None

    def test_chat_request_with_context(self):
        ctx = SensorContext(battery_level=80, activity="still", location_zone="home")
        req = ChatRequest(message="test", context=ctx, session_id="abc123")
        assert req.context.battery_level == 80
        assert req.session_id == "abc123"

    def test_chat_response_defaults(self):
        resp = ChatResponse(reply="Hello back")
        assert resp.reply == "Hello back"
        assert resp.confidence_score == 1.0
        assert resp.detected_mood is None


class TestEvolutionSchemas:
    def test_proposal_status_enum(self):
        assert ProposalStatus.PENDING  == "PENDING"
        assert ProposalStatus.AWAITING == "AWAITING"
        assert ProposalStatus.APPROVED == "APPROVED"
        assert ProposalStatus.REJECTED == "REJECTED"
        assert ProposalStatus.FAILED   == "FAILED"

    def test_upgrade_proposal_creation(self):
        p = UpgradeProposal(
            proposal_id="abc",
            instruction="Add logging",
            target_file="main.py",
            branch_name="upgrade/abc",
            status=ProposalStatus.PENDING,
            created_at=time.time(),
            updated_at=time.time()
        )
        assert p.proposal_id == "abc"
        assert p.status == ProposalStatus.PENDING
        assert p.diff_preview is None
