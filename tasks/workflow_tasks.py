from typing import Dict, Any, List, Optional
from crewai import Task
from database.models import LeaseExit, WorkflowStatus
from utils.tools import DatabaseTool
from agents.workflow_designer import WorkflowDesignerAgent
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WorkflowTasks:
    """Tasks for managing workflows"""
    
    def __init__(self):
        """Initialize workflow tasks"""
        self.db_tool = DatabaseTool()
        self.workflow_agent = WorkflowDesignerAgent()
    
    async def create_workflow_task(self, workflow_type: str, 
                                  requirements: Dict[str, Any]) -> Task:
        """Create a task for designing a workflow
        
        Args:
            workflow_type: The type of workflow
            requirements: The workflow requirements
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Design a {workflow_type} workflow based on requirements",
            agent=self.workflow_agent.get_agent(),
            context={
                "workflow_type": workflow_type,
                "requirements": requirements
            }
        )
    
    async def update_workflow_status_task(self, lease_exit_id: str, 
                                        status: WorkflowStatus, 
                                        comments: Optional[str] = None) -> Task:
        """Create a task for updating a workflow status
        
        Args:
            lease_exit_id: The ID of the lease exit
            status: The new status
            comments: Optional comments
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Update the status of lease exit {lease_exit_id} to {status}",
            agent=self.workflow_agent.get_agent(),
            context={
                "lease_exit_id": lease_exit_id,
                "status": status,
                "comments": comments
            }
        )
    
    async def execute_update_workflow_status(self, lease_exit_id: str, 
                                           status: WorkflowStatus, 
                                           comments: Optional[str] = None) -> Dict[str, Any]:
        """Execute a workflow status update
        
        Args:
            lease_exit_id: The ID of the lease exit
            status: The new status
            comments: Optional comments
            
        Returns:
            Dict: The execution result
        """
        try:
            # Get the lease exit
            lease_exit = await self.db_tool.get_lease_exit(lease_exit_id)
            if not lease_exit:
                logger.error(f"Lease exit {lease_exit_id} not found")
                return {
                    "success": False,
                    "message": f"Lease exit {lease_exit_id} not found"
                }
            
            # Update the status
            lease_exit.status = status
            lease_exit.updated_at = datetime.utcnow()
            
            # Add comments if provided
            if comments:
                if not lease_exit.metadata:
                    lease_exit.metadata = {}
                
                lease_exit.metadata["status_change_comments"] = comments
                lease_exit.metadata["status_change_timestamp"] = datetime.utcnow().isoformat()
            
            # Save the updated lease exit
            await self.db_tool.update_lease_exit(lease_exit)
            
            logger.info(f"Updated status of lease exit {lease_exit_id} to {status}")
            
            return {
                "success": True,
                "message": f"Updated status to {status}",
                "lease_exit_id": lease_exit_id,
                "status": status
            }
        
        except Exception as e:
            logger.error(f"Error updating workflow status: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating workflow status: {str(e)}"
            }
    
    async def initiate_lease_exit_task(self, lease_exit_data: Dict[str, Any]) -> Task:
        """Create a task for initiating a lease exit
        
        Args:
            lease_exit_data: The lease exit data
            
        Returns:
            Task: The created task
        """
        return Task(
            description="Initiate a new lease exit process",
            agent=self.workflow_agent.get_agent(),
            context={
                "lease_exit_data": lease_exit_data
            }
        )
    
    async def execute_initiate_lease_exit(self, lease_exit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the initiation of a lease exit
        
        Args:
            lease_exit_data: The lease exit data
            
        Returns:
            Dict: The execution result
        """
        try:
            # Create the lease exit
            property_details = {
                "property_address": lease_exit_data.get("property_address", "N/A"),
                "lease_id": lease_exit_data.get("lease_id", "N/A")
            }
            
            lease_exit = LeaseExit(
                lease_id=lease_exit_data.get("lease_id"),
                property_details=property_details,
                status=WorkflowStatus.DRAFT,
                current_step="initiate_lease_exit",
                created_by=lease_exit_data.get("created_by", "system"),
                metadata={
                    "exit_date": lease_exit_data.get("exit_date"),
                    "reason_for_exit": lease_exit_data.get("reason_for_exit"),
                    "additional_notes": lease_exit_data.get("additional_notes", "")
                }
            )
            
            # Save the lease exit
            created_lease_exit = await self.db_tool.create_lease_exit(lease_exit.dict())
            
            logger.info(f"Created new lease exit with ID {created_lease_exit.id}")
            
            return {
                "success": True,
                "message": "Lease exit initiated successfully",
                "lease_exit_id": created_lease_exit.id,
                "status": created_lease_exit.status
            }
        
        except Exception as e:
            logger.error(f"Error initiating lease exit: {str(e)}")
            return {
                "success": False,
                "message": f"Error initiating lease exit: {str(e)}"
            }
