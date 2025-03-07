from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from database.models import StakeholderRole
from agents.approval_architect import ApprovalArchitectAgent

router = APIRouter()

@router.post("/{lease_exit_id}/process")
async def process_approval(
    lease_exit_id: str,
    approver_role: StakeholderRole,
    approved: bool,
    comments: str = None
) -> Dict[str, Any]:
    """Process an approval decision
    
    Args:
        lease_exit_id: The ID of the lease exit
        approver_role: The role of the approver
        approved: Whether the lease exit is approved
        comments: Optional comments
        
    Returns:
        Dict: Processing result
    """
    try:
        approval_agent = ApprovalArchitectAgent()
        result = await approval_agent.process_approval(
            lease_exit_id=lease_exit_id,
            approver_role=approver_role,
            approved=approved,
            comments=comments
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {str(e)}")

@router.post("/{lease_exit_id}/chain")
async def create_approval_chain(
    lease_exit_id: str,
    required_approvers: List[StakeholderRole]
) -> Dict[str, Any]:
    """Create an approval chain for a lease exit
    
    Args:
        lease_exit_id: The ID of the lease exit
        required_approvers: List of roles required for approval
        
    Returns:
        Dict: The created approval chain
    """
    try:
        approval_agent = ApprovalArchitectAgent()
        approval_chain = await approval_agent.create_approval_chain(
            lease_exit_id=lease_exit_id,
            required_approvers=required_approvers
        )
        return {"status": "success", "approval_chain": approval_chain}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create approval chain: {str(e)}")

@router.get("/{lease_exit_id}/status")
async def get_approval_status(lease_exit_id: str) -> Dict[str, Any]:
    """Get the approval status for a lease exit
    
    Args:
        lease_exit_id: The ID of the lease exit
        
    Returns:
        Dict: The approval status
    """
    # This is a placeholder implementation
    # You would typically query the database to get the actual status
    return {
        "status": "pending",
        "message": "Approval status endpoint not yet implemented"
    } 