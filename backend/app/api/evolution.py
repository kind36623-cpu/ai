"""
Layer 16: Full Approval Gate API
Handles the entire lifecycle: trigger → sandbox → test → await → approve/reject
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import UpgradeProposalRequest, ProposalStatus
from app.evolution.proposal_store import proposal_store, UpgradeProposal
from app.evolution.git_manager import git_manager
from app.evolution.code_editor import code_editor
from app.evolution.evaluator import evaluator
import subprocess
import time
import uuid
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Background Evolution Cycle ────────────────────────────────────────────────

def _run_evolution_cycle(proposal_id: str):
    """
    Full self-evolution cycle run as a background task:
    1. Create sandbox branch
    2. Ask AI to write improved code
    3. Apply code to files
    4. Run tests
    5. If pass → mark AWAITING (user must approve)
       If fail → mark FAILED and discard branch
    """
    p = proposal_store.get(proposal_id)
    if not p:
        return

    try:
        # Step 1 — Sandbox
        proposal_store.update_status(proposal_id, ProposalStatus.PENDING)
        branch_created = git_manager.create_upgrade_branch(p.branch_name)
        if not branch_created:
            proposal_store.update_status(proposal_id, ProposalStatus.FAILED,
                                         test_output="Failed to create sandbox branch.")
            return

        # Step 2 — Code Editor (run sync inside thread)
        new_code = asyncio.run(code_editor.propose_upgrade(p.target_file, p.instruction))
        if not new_code:
            git_manager.discard_upgrade()
            proposal_store.update_status(proposal_id, ProposalStatus.FAILED,
                                         test_output="AI failed to generate new code.")
            return

        # Step 3 — Apply Edit
        code_editor.apply_edit(p.target_file, new_code)

        # Step 4 — Get diff for preview
        try:
            diff_result = subprocess.run(
                ["git", "diff"], cwd=".", capture_output=True, text=True
            )
            diff_preview = diff_result.stdout[:3000]  # Limit size
        except Exception:
            diff_preview = "Diff not available."

        # Step 5 — Test
        proposal_store.update_status(proposal_id, ProposalStatus.TESTING)
        tests_passed, test_output = evaluator.run_tests()

        if tests_passed:
            git_manager.commit_changes(f"[AutoUpgrade] {p.instruction}")
            proposal_store.update_status(
                proposal_id,
                ProposalStatus.AWAITING,
                diff_preview=diff_preview,
                test_output=test_output
            )
            logger.info(f"Proposal {proposal_id} is ready for your approval.")
        else:
            # Auto-discard bad code — safety gate
            git_manager.discard_upgrade()
            proposal_store.update_status(
                proposal_id,
                ProposalStatus.FAILED,
                test_output=test_output
            )
            logger.warning(f"Proposal {proposal_id} failed tests. Auto-discarded.")

    except Exception as e:
        logger.error(f"Evolution cycle error: {e}")
        git_manager.discard_upgrade()
        proposal_store.update_status(proposal_id, ProposalStatus.FAILED, test_output=str(e))


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/trigger", summary="Trigger a self-improvement cycle")
async def trigger_upgrade(req: UpgradeProposalRequest, background_tasks: BackgroundTasks):
    """
    Layer 13: Starts an autonomous upgrade cycle in the background.
    No code is changed on master until you explicitly approve.
    """
    proposal_id = str(uuid.uuid4())[:8]
    branch_name = f"upgrade/{proposal_id}"

    proposal = UpgradeProposal(
        proposal_id=proposal_id,
        instruction=req.instruction,
        target_file=req.target_file,
        branch_name=branch_name,
        status=ProposalStatus.PENDING,
        created_at=time.time(),
        updated_at=time.time()
    )
    proposal_store.create(proposal)

    # Run in background — non-blocking
    background_tasks.add_task(_run_evolution_cycle, proposal_id)

    return {
        "proposal_id": proposal_id,
        "branch": branch_name,
        "status": "Upgrade cycle started. Poll /evolution/status/{id} for updates."
    }


@router.get("/status/{proposal_id}", summary="Check upgrade proposal status")
async def get_status(proposal_id: str):
    """Poll this to see if the AI's upgrade is ready for your review."""
    p = proposal_store.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return p


@router.get("/pending", summary="List all proposals awaiting your approval")
async def list_pending():
    """Returns all upgrade proposals that passed tests and need your approval."""
    return proposal_store.list_awaiting()


@router.get("/all", summary="Full proposal history")
async def list_all():
    return proposal_store.list_all()


@router.post("/approve/{proposal_id}", summary="APPROVE an AI upgrade")
async def approve_upgrade(proposal_id: str):
    """
    Layer 16: The Approval Gate.
    If you approve, the sandbox branch is merged to master.
    """
    p = proposal_store.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if p.status != ProposalStatus.AWAITING:
        raise HTTPException(status_code=400, detail=f"Proposal is not awaiting approval. Current status: {p.status}")

    success = git_manager.merge_upgrade(p.branch_name)
    if success:
        proposal_store.update_status(proposal_id, ProposalStatus.APPROVED)
        return {
            "status": "APPROVED",
            "message": "Upgrade merged to master. Restart the backend server to apply changes."
        }
    else:
        raise HTTPException(status_code=500, detail="Merge failed. Manual intervention needed.")


@router.post("/reject/{proposal_id}", summary="REJECT an AI upgrade")
async def reject_upgrade(proposal_id: str):
    """
    Layer 16: Rejection Gate.
    Discards the sandbox branch. Master is untouched.
    """
    p = proposal_store.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    git_manager.discard_upgrade()
    proposal_store.update_status(proposal_id, ProposalStatus.REJECTED)
    return {"status": "REJECTED", "message": "Upgrade discarded. Your system is unchanged."}
