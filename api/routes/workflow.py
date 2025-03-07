from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List, Optional
from database.models import LeaseExit, FormData, WorkflowStatus, StakeholderRole
from workflows.lease_exit_flow import LeaseExitCrew
from utils.tools import DatabaseTool, FormValidationTool
from pydantic import BaseModel, ValidationError
from database.connection import get_database
import logging
from datetime import datetime
from fastapi.responses import JSONResponse
import json
from bson import ObjectId

router = APIRouter()
lease_exit_crew = LeaseExitCrew()
db_tool = DatabaseTool()
form_tool = FormValidationTool()
logger = logging.getLogger(__name__)

class LeaseExitRequest(BaseModel):
    lease_id: str
    property_address: str
    exit_date: str
    reason_for_exit: str
    additional_notes: str = ""

class FormSubmissionRequest(BaseModel):
    form_type: str
    data: Dict[str, Any]
    submitted_by: str

class ApprovalRequest(BaseModel):
    approver_id: str
    decision: str
    comments: str

# Add a custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

@router.post("/lease-exit", status_code=201)
async def create_lease_exit(request: Request):
    """Create a new lease exit workflow"""
    try:
        # Get the request data
        request_data = await request.json()
        logger.info(f"Received lease exit creation request: {request_data}")
        
        # Create the lease exit workflow
        workflow = LeaseExitCrew()
        result = await workflow.create_lease_exit_workflow(request_data)
        logger.info(f"Lease exit workflow creation result: {result}")
        
        # Check if the workflow creation was successful
        if result.get("success"):
            # Prepare the response data
            response_data = {
                "status": "success",
                "message": result.get("message", "Lease exit created successfully"),
                "lease_exit_id": result.get("lease_exit_id"),
                "data": result.get("data", {})
            }
            
            # Serialize the response data using the custom encoder
            serialized_data = json.loads(json.dumps(response_data, cls=DateTimeEncoder))
            
            # Return the successful result
            return JSONResponse(
                status_code=201,
                content=serialized_data
            )
        else:
            # Prepare the error response
            error_response = {
                "status": "error",
                "message": "Failed to create lease exit",
                "error": result.get("error", "Unknown error")
            }
            
            # Serialize the error response
            serialized_error = json.loads(json.dumps(error_response, cls=DateTimeEncoder))
            
            # Return the error with appropriate status code
            return JSONResponse(
                status_code=400,
                content=serialized_error
            )
    except Exception as e:
        # Log the error and return a 500 response
        logger.error(f"Error creating lease exit: {str(e)}", exc_info=True)
        
        # Prepare the exception response
        exception_response = {
            "status": "error",
            "message": "An unexpected error occurred",
            "error": str(e)
        }
        
        # Serialize the exception response
        serialized_exception = json.loads(json.dumps(exception_response, cls=DateTimeEncoder))
        
        return JSONResponse(
            status_code=500,
            content=serialized_exception
        )

@router.post("/lease-exit/{lease_exit_id}/form")
async def submit_form(
    lease_exit_id: str,
    request: FormSubmissionRequest,
    db=Depends(get_database)
):
    """Submit a form for a lease exit"""
    try:
        logger.info(f"Received form submission for lease exit {lease_exit_id}: {request}")
        
        # Convert the request to a dictionary
        form_data = request.model_dump()
        
        # Extract the form data and role
        form_type = form_data.get("form_type")
        submitted_data = form_data.get("data", {})
        submitted_by = form_data.get("submitted_by")
        
        logger.info(f"Processing form submission: type={form_type}, submitted_by={submitted_by}")
        
        # Initialize the lease exit workflow
        workflow = LeaseExitCrew()
        
        # Handle the form submission
        result = await workflow.handle_form_submission(
            lease_exit_id=lease_exit_id,
            form_data=submitted_data,
            role=submitted_by
        )
        
        logger.info(f"Form submission result: {result}")
        
        # Check if the form submission was successful
        if result.get("success"):
            # Serialize the response data using the custom encoder
            response_data = json.loads(json.dumps(result, cls=DateTimeEncoder))
            
            # Return the successful result
            return JSONResponse(
                status_code=200,
                content=response_data
            )
        else:
            # Serialize the error response
            error_response = json.loads(json.dumps({
                "status": "error",
                "message": "Failed to process form submission",
                "error": result.get("error", "Unknown error"),
                "details": result.get("details", [])
            }, cls=DateTimeEncoder))
            
            # Return the error with appropriate status code
            return JSONResponse(
                status_code=400,
                content=error_response
            )
    except Exception as e:
        # Log the error and return a 500 response
        logger.error(f"Error processing form submission: {str(e)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred",
                "error": str(e)
            }
        )

@router.post("/lease-exit/{lease_exit_id}/approve")
async def submit_approval(
    lease_exit_id: str,
    request: ApprovalRequest,
    db=Depends(get_database)
):
    """Submit an approval decision for a lease exit"""
    try:
        logger.info(f"Received approval request for lease exit {lease_exit_id}: {request}")
        
        # Convert the request to a dictionary
        approval_data = request.model_dump()
        
        logger.info(f"Processing approval request from: {approval_data.get('approver_id')}")
        
        # Initialize the lease exit workflow
        workflow = LeaseExitCrew()
        
        # Handle the approval request
        result = await workflow.handle_approval_request(
            lease_exit_id=lease_exit_id,
            approval_data=approval_data
        )
        
        logger.info(f"Approval request result: {result}")
        
        # Check if the approval request was successful
        if result.get("success"):
            # Serialize the response data using the custom encoder
            response_data = json.loads(json.dumps(result, cls=DateTimeEncoder))
            
            # Return the successful result
            return JSONResponse(
                status_code=200,
                content=response_data
            )
        else:
            # Serialize the error response
            error_response = json.loads(json.dumps({
                "status": "error",
                "message": "Failed to process approval request",
                "error": result.get("error", "Unknown error"),
                "details": result.get("details", [])
            }, cls=DateTimeEncoder))
            
            # Return the error with appropriate status code
            return JSONResponse(
                status_code=400,
                content=error_response
            )
    except Exception as e:
        # Log the error and return a 500 response
        logger.error(f"Error processing approval request: {str(e)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred",
                "error": str(e)
            }
        )

@router.get("/lease-exit/{lease_exit_id}", response_model=LeaseExit)
async def get_lease_exit(lease_exit_id: str, db=Depends(get_database)):
    """Get a specific lease exit workflow"""
    lease_exit = await db_tool.get_lease_exit._run(lease_exit_id)
    if not lease_exit:
        raise HTTPException(status_code=404, detail="Lease exit not found")
    
    # Convert to JSON-serializable format
    lease_exit_dict = json.loads(json.dumps(lease_exit, cls=DateTimeEncoder))
    return JSONResponse(
        status_code=200,
        content=lease_exit_dict
    )

@router.get("/lease-exits", response_model=List[LeaseExit])
async def list_lease_exits(db=Depends(get_database)):
    """List all lease exit workflows"""
    try:
        lease_exits = await db.lease_exits.find().to_list(length=100)
        
        # Convert _id to string id for each document
        for doc in lease_exits:
            doc["id"] = str(doc.pop("_id"))
        
        # Convert to JSON-serializable format
        lease_exits_dict = json.loads(json.dumps(lease_exits, cls=DateTimeEncoder))
        return JSONResponse(
            status_code=200,
            content=lease_exits_dict
        )
    except Exception as e:
        logger.error(f"Error listing lease exits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
