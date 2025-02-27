from typing import Dict, Any, List, Optional
from crewai import Task
from database.models import ApprovalStep, StakeholderRole, WorkflowStatus
from utils.tools import DatabaseTool, NotificationTool
from agents.approval_architect import ApprovalArchitectAgent
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ApprovalTasks:
    """Tasks for managing approval processes"""
    
    def __init__(self):
        """Initialize approval tasks"""
        self.db_tool = DatabaseTool()
        self.notification_tool = NotificationTool()
        self.approval_agent = ApprovalArchitectAgent()
    
    async def create_approval_chain_task(self, lease_exit_id: str, 
                                       required_approvers: List[StakeholderRole]) -> Task:
        """Create a task for creating an approval chain
        
        Args:
            lease_exit_id: The ID of the lease exit
            required_approvers: List of roles required for approval
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Create approval chain for lease exit {lease_exit_id}",
            agent=self.approval_agent.get_agent(),
            context={
                "lease_exit_id": lease_exit_id,
                "required_approvers": required_approvers
            }
        )
    
    async def execute_create_approval_chain(self, lease_exit_id: str, 
                                          required_approvers: List[StakeholderRole]) -> Dict[str, Any]:
        """Execute the creation of an approval chain
        
        Args:
            lease_exit_id: The ID of the lease exit
            required_approvers: List of roles required for approval
            
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
            
            # Create the approval chain
            approval_chain = []
            for role in required_approvers:
                approval_step = ApprovalStep(
                    role=role,
                    status="pending"
                )
                approval_chain.append(approval_step)
            
            # Update the lease exit
            lease_exit.approval_chain = approval_chain
            lease_exit.status = WorkflowStatus.PENDING_APPROVAL
            lease_exit.updated_at = datetime.utcnow()
            
            await self.db_tool.update_lease_exit(lease_exit)
            
            # Notify approvers
            await self.notify_approvers(lease_exit_id, required_approvers)
            
            logger.info(f"Created approval chain for lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": "Approval chain created successfully",
                "approval_chain": [step.dict() for step in approval_chain]
            }
        
        except Exception as e:
            logger.error(f"Error creating approval chain: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating approval chain: {str(e)}"
            }
    
    async def process_approval_task(self, lease_exit_id: str, approver_role: StakeholderRole, 
                                  approved: bool, comments: Optional[str] = None) -> Task:
        """Create a task for processing an approval decision
        
        Args:
            lease_exit_id: The ID of the lease exit
            approver_role: The role of the approver
            approved: Whether the lease exit is approved
            comments: Optional comments
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Process approval decision for lease exit {lease_exit_id}",
            agent=self.approval_agent.get_agent(),
            context={
                "lease_exit_id": lease_exit_id,
                "approver_role": approver_role,
                "approved": approved,
                "comments": comments
            }
        )
    
    async def execute_process_approval(self, lease_exit_id: str, approver_role: StakeholderRole, 
                                     approved: bool, comments: Optional[str] = None) -> Dict[str, Any]:
        """Execute the processing of an approval decision
        
        Args:
            lease_exit_id: The ID of the lease exit
            approver_role: The role of the approver
            approved: Whether the lease exit is approved
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
            
            # Find the approval step for the role
            step_found = False
            for step in lease_exit.approval_chain:
                if step.role == approver_role:
                    step.status = "approved" if approved else "rejected"
                    step.approved_by = approver_role.value  # This could be a user ID in a real system
                    step.approved_at = datetime.utcnow()
                    step.comments = comments
                    step_found = True
                    break
            
            if not step_found:
                logger.error(f"Approval step for role {approver_role} not found")
                return {
                    "success": False,
                    "message": f"Approval step for role {approver_role} not found"
                }
            
            # Check if all approvals are complete
            all_approved = all(step.status == "approved" for step in lease_exit.approval_chain)
            any_rejected = any(step.status == "rejected" for step in lease_exit.approval_chain)
            
            # Update lease exit status
            if any_rejected:
                lease_exit.status = WorkflowStatus.REVIEW_NEEDED
                await self.notify_rejection(lease_exit_id, approver_role, comments)
            elif all_approved:
                lease_exit.status = WorkflowStatus.READY_FOR_EXIT
                await self.notify_approval_complete(lease_exit_id)
            
            # Update the lease exit
            lease_exit.updated_at = datetime.utcnow()
            await self.db_tool.update_lease_exit(lease_exit)
            
            logger.info(f"Processed approval decision for lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": "Approval decision processed successfully",
                "status": lease_exit.status
            }
        
        except Exception as e:
            logger.error(f"Error processing approval decision: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing approval decision: {str(e)}"
            }
    
    async def notify_approvers(self, lease_exit_id: str, approver_roles: List[StakeholderRole]) -> Dict[str, Any]:
        """Notify approvers about a pending approval
        
        Args:
            lease_exit_id: The ID of the lease exit
            approver_roles: List of approver roles to notify
            
        Returns:
            Dict: The notification result
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
            
            property_address = lease_exit.property_details.get("property_address", "N/A")
            
            message = f"""
            <p>You have a pending approval for Lease Exit (ID: {lease_exit_id}).</p>
            <p><strong>Property:</strong> {property_address}</p>
            <p>Please review and provide your approval decision.</p>
            <p>You can access the lease exit details and approval form at: /lease-exits/{lease_exit_id}</p>
            """
            
            # Notify all approvers
            await self.notification_tool.notify_stakeholders(
                lease_exit_id,
                [role.value for role in approver_roles],
                message
            )
            
            logger.info(f"Notified approvers for lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": "Approvers notified successfully",
                "notified_roles": [role.value for role in approver_roles]
            }
        
        except Exception as e:
            logger.error(f"Error notifying approvers: {str(e)}")
            return {
                "success": False,
                "message": f"Error notifying approvers: {str(e)}"
            }
    
    async def notify_rejection(self, lease_exit_id: str, rejector_role: StakeholderRole, 
                             comments: Optional[str] = None) -> Dict[str, Any]:
        """Notify about a rejection
        
        Args:
            lease_exit_id: The ID of the lease exit
            rejector_role: The role that rejected
            comments: Optional rejection comments
            
        Returns:
            Dict: The notification result
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
            
            property_address = lease_exit.property_details.get("property_address", "N/A")
            
            message = f"""
            <p>A lease exit approval has been rejected.</p>
            <p><strong>Lease Exit ID:</strong> {lease_exit_id}</p>
            <p><strong>Property:</strong> {property_address}</p>
            <p><strong>Rejected by:</strong> {rejector_role.value}</p>
            """
            
            if comments:
                message += f"<p><strong>Comments:</strong> {comments}</p>"
            
            message += """
            <p>Please review the lease exit information and make necessary corrections before resubmitting for approval.</p>
            """
            
            # Notify the Lease Exit Management Team
            await self.notification_tool.notify_stakeholders(
                lease_exit_id,
                [StakeholderRole.LEASE_EXIT_MANAGEMENT.value],
                message
            )
            
            logger.info(f"Notified about rejection for lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": "Rejection notification sent successfully"
            }
        
        except Exception as e:
            logger.error(f"Error sending rejection notification: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending rejection notification: {str(e)}"
            }
    
    async def notify_approval_complete(self, lease_exit_id: str) -> Dict[str, Any]:
        """Notify that all approvals are complete
        
        Args:
            lease_exit_id: The ID of the lease exit
            
        Returns:
            Dict: The notification result
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
            
            property_address = lease_exit.property_details.get("property_address", "N/A")
            
            message = f"""
            <p>All approvals have been received for Lease Exit (ID: {lease_exit_id}).</p>
            <p><strong>Property:</strong> {property_address}</p>
            <p>The lease exit is now marked as Ready for Exit.</p>
            <p>You can access the lease exit details at: /lease-exits/{lease_exit_id}</p>
            """
            
            # Notify all stakeholders
            roles = [role.value for role in StakeholderRole]
            await self.notification_tool.notify_stakeholders(
                lease_exit_id,
                roles,
                message
            )
            
            logger.info(f"Notified all stakeholders about completed approvals for lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": "Approval completion notification sent successfully"
            }
        
        except Exception as e:
            logger.error(f"Error sending approval completion notification: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending approval completion notification: {str(e)}"
            }
