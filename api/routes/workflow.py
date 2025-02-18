from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from database.models import LeaseExit, FormData, WorkflowStatus, StakeholderRole
from workflows.lease_exit_flow import LeaseExitWorkflow
from utils.tools import DatabaseTool, FormValidationTool
from pydantic import BaseModel

router = APIRouter()
workflow = LeaseExitWorkflow()
db_tool = DatabaseTool()
form_tool = FormValidationTool()

class LeaseExitRequest(BaseModel):
    lease_id: str
    property_address: str
    exit_date: str
    reason_for_exit: str
    additional_details: Dict[str, Any] = {}

class FormSubmissionRequest(BaseModel):
    form_type: str
    data: Dict[str, Any]
    submitted_by: str

class ApprovalRequest(BaseModel):
    approver_id: str
    decision: str
    comments: str

@router.post("/lease-exit", response_model=LeaseExit)
async def create_lease_exit(request: LeaseExitRequest):
    """Create a new lease exit workflow instance"""
    # Validate the initial form data
    validation_result = form_tool.validate_initial_form(request.dict())
    if not validation_result["is_valid"]:
        raise HTTPException(status_code=400, detail=validation_result["errors"])
    
    # Create lease exit workflow instance
    lease_exit = await workflow.execute_workflow(request.dict())
    return lease_exit

@router.post("/lease-exit/{lease_exit_id}/form", response_model=FormData)
async def submit_form(
    lease_exit_id: str,
    request: FormSubmissionRequest
):
    """Submit a form for a specific lease exit workflow"""
    # Get the lease exit instance
    lease_exit = await db_tool.get_lease_exit(lease_exit_id)
    if not lease_exit:
        raise HTTPException(status_code=404, detail="Lease exit not found")
    
    # Validate form data based on form type
    validation_method = getattr(
        form_tool,
        f"validate_{request.form_type.lower()}_form",
        form_tool.validate_initial_form
    )
    validation_result = validation_method(request.data)
    
    if not validation_result["is_valid"]:
        raise HTTPException(status_code=400, detail=validation_result["errors"])
    
    # Create form submission
    form_data = await db_tool.create_form(
        lease_exit_id,
        {
            "form_type": request.form_type,
            "data": request.data,
            "submitted_by": request.submitted_by,
            "status": "submitted"
        }
    )
    
    # Handle form submission in workflow
    await workflow.handle_form_submission(
        lease_exit_id,
        form_data.dict(),
        StakeholderRole(request.submitted_by)
    )
    
    return form_data

@router.post("/lease-exit/{lease_exit_id}/approve")
async def submit_approval(
    lease_exit_id: str,
    request: ApprovalRequest
):
    """Submit an approval decision for a lease exit workflow"""
    # Validate approval data
    validation_result = form_tool.validate_approval(request.dict())
    if not validation_result["is_valid"]:
        raise HTTPException(status_code=400, detail=validation_result["errors"])
    
    # Get the lease exit instance
    lease_exit = await db_tool.get_lease_exit(lease_exit_id)
    if not lease_exit:
        raise HTTPException(status_code=404, detail="Lease exit not found")
    
    # Handle approval in workflow
    result = await workflow.handle_approval_request(lease_exit_id)
    
    # Update lease exit status based on approval decision
    if request.decision == "approve":
        if all(step.status == "approved" for step in lease_exit.approval_chain):
            lease_exit.status = WorkflowStatus.READY_FOR_EXIT
        else:
            lease_exit.status = WorkflowStatus.PENDING_APPROVAL
    else:
        lease_exit.status = WorkflowStatus.REVIEW_NEEDED
    
    await db_tool.update_lease_exit(lease_exit)
    return {"status": "success", "message": "Approval submitted successfully"}

@router.get("/lease-exit/{lease_exit_id}", response_model=LeaseExit)
async def get_lease_exit(lease_exit_id: str):
    """Get details of a specific lease exit workflow"""
    lease_exit = await db_tool.get_lease_exit(lease_exit_id)
    if not lease_exit:
        raise HTTPException(status_code=404, detail="Lease exit not found")
    return lease_exit

@router.get("/lease-exits", response_model=List[LeaseExit])
async def list_lease_exits():
    """List all lease exit workflows"""
    cursor = db_tool.db.lease_exits.find()
    lease_exits = []
    async for doc in cursor:
        lease_exits.append(LeaseExit(**doc))
    return lease_exits
