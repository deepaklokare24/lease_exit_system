from crewai import Agent
from utils.tools import DatabaseTool, NotificationTool
import os
from typing import List, Dict, Any
from database.models import ApprovalStep, StakeholderRole, WorkflowStatus

class ApprovalArchitectAgent:
    """Agent responsible for designing and managing approval processes"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the approval architect agent
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.db_tool = DatabaseTool()
        self.notification_tool = NotificationTool()
    
    def get_agent(self) -> Agent:
        """Create and return the Crew AI agent instance
        
        Returns:
            Agent: The Crew AI agent instance
        """
        return Agent(
            role="Approval Process Architect",
            goal="Design compliant approval processes for workflow steps",
            backstory="Expert in creating robust approval mechanisms that ensure proper sign-off",
            verbose=True,
            allow_delegation=False,
            tools=[self.db_tool, self.notification_tool],
            llm=os.getenv("AI_MODEL", "anthropic/claude-3-5-sonnet-20241022")
        )
    
    async def create_approval_chain(self, lease_exit_id: str, required_approvers: List[StakeholderRole]) -> List[ApprovalStep]:
        """Create an approval chain for a lease exit workflow
        
        Args:
            lease_exit_id: The ID of the lease exit
            required_approvers: List of roles required for approval
            
        Returns:
            List[ApprovalStep]: The created approval chain
        """
        # Get the lease exit
        lease_exit = await self.db_tool.get_lease_exit(lease_exit_id)
        if not lease_exit:
            raise ValueError(f"Lease exit with ID {lease_exit_id} not found")
        
        # Create approval steps
        approval_chain = []
        for role in required_approvers:
            approval_step = ApprovalStep(
                role=role,
                status="pending"
            )
            approval_chain.append(approval_step)
        
        # Update the lease exit with the approval chain
        lease_exit.approval_chain = approval_chain
        lease_exit.status = WorkflowStatus.PENDING_APPROVAL
        await self.db_tool.update_lease_exit(lease_exit)
        
        # Notify all approvers
        await self.notify_approvers(lease_exit_id, required_approvers)
        
        return approval_chain
    
    async def process_approval(self, lease_exit_id: str, approver_role: StakeholderRole, 
                              approved: bool, comments: str = None) -> Dict[str, Any]:
        """Process an approval decision
        
        Args:
            lease_exit_id: The ID of the lease exit
            approver_role: The role of the approver
            approved: Whether the lease exit is approved
            comments: Optional comments
            
        Returns:
            Dict: Processing result
        """
        # Get the lease exit
        lease_exit = await self.db_tool.get_lease_exit(lease_exit_id)
        if not lease_exit:
            raise ValueError(f"Lease exit with ID {lease_exit_id} not found")
        
        # Find the approval step for the role
        for step in lease_exit.approval_chain:
            if step.role == approver_role:
                step.status = "approved" if approved else "rejected"
                step.comments = comments
                step.approved_at = datetime.utcnow()
                break
        
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
        await self.db_tool.update_lease_exit(lease_exit)
        
        return {
            "status": "success",
            "lease_exit_status": lease_exit.status,
            "message": "Approval processed successfully"
        }
    
    async def notify_approvers(self, lease_exit_id: str, approver_roles: List[StakeholderRole]):
        """Notify approvers about a pending approval
        
        Args:
            lease_exit_id: The ID of the lease exit
            approver_roles: List of approver roles to notify
        """
        lease_exit = await self.db_tool.get_lease_exit(lease_exit_id)
        if not lease_exit:
            raise ValueError(f"Lease exit with ID {lease_exit_id} not found")
        
        property_address = lease_exit.property_details.get("property_address", "N/A")
        
        message = f"""
        <p>You have a pending approval for Lease Exit (ID: {lease_exit_id}).</p>
        <p><strong>Property:</strong> {property_address}</p>
        <p>Please review and provide your approval decision.</p>
        <p>You can access the lease exit details and approval form at: /lease-exits/{lease_exit_id}</p>
        """
        
        await self.notification_tool.notify_stakeholders(
            lease_exit_id,
            [role.value for role in approver_roles],
            message
        )
    
    async def notify_rejection(self, lease_exit_id: str, rejector_role: StakeholderRole, comments: str = None):
        """Notify about a rejection
        
        Args:
            lease_exit_id: The ID of the lease exit
            rejector_role: The role that rejected
            comments: Optional rejection comments
        """
        lease_exit = await self.db_tool.get_lease_exit(lease_exit_id)
        if not lease_exit:
            raise ValueError(f"Lease exit with ID {lease_exit_id} not found")
        
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
    
    async def notify_approval_complete(self, lease_exit_id: str):
        """Notify that all approvals are complete
        
        Args:
            lease_exit_id: The ID of the lease exit
        """
        lease_exit = await self.db_tool.get_lease_exit(lease_exit_id)
        if not lease_exit:
            raise ValueError(f"Lease exit with ID {lease_exit_id} not found")
        
        property_address = lease_exit.property_details.get("property_address", "N/A")
        
        message = f"""
        <p>All approvals have been received for Lease Exit (ID: {lease_exit_id}).</p>
        <p><strong>Property:</strong> {property_address}</p>
        <p>The lease exit is now marked as Ready for Exit.</p>
        <p>You can access the lease exit details at: /lease-exits/{lease_exit_id}</p>
        """
        
        # Notify the Lease Exit Management Team
        await self.notification_tool.notify_stakeholders(
            lease_exit_id,
            [StakeholderRole.LEASE_EXIT_MANAGEMENT.value],
            message
        )
        
        # Also notify all other stakeholders who were in the approval chain
        approver_roles = [step.role.value for step in lease_exit.approval_chain]
        await self.notification_tool.notify_stakeholders(
            lease_exit_id,
            approver_roles,
            message
        )
