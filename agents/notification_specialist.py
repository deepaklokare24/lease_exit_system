from crewai import Agent
from utils.tools import NotificationTool, DatabaseTool
import os
from typing import List, Dict, Any
from database.models import StakeholderRole, Notification
from datetime import datetime

class NotificationSpecialistAgent:
    """Agent responsible for managing notifications and communications to stakeholders"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the notification specialist agent
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.notification_tool = NotificationTool()
        self.db_tool = DatabaseTool()
    
    def get_agent(self) -> Agent:
        """Create and return the Crew AI agent instance
        
        Returns:
            Agent: The Crew AI agent instance
        """
        return Agent(
            role="Notification Specialist",
            goal="Ensure timely and effective communications to all stakeholders",
            backstory="Expert in crafting clear notifications and ensuring they reach the right people",
            verbose=True,
            allow_delegation=False,
            tools=[self.notification_tool, self.db_tool],
            llm=os.getenv("AI_MODEL", "anthropic/claude-3-sonnet-20240229")
        )
    
    async def create_notification(self, lease_exit_id: str, recipient_role: StakeholderRole, 
                                 subject: str, message: str, notification_type: str = "update") -> Notification:
        """Create and send a notification
        
        Args:
            lease_exit_id: The ID of the lease exit
            recipient_role: The role of the recipient
            subject: The notification subject
            message: The notification message
            notification_type: The type of notification
            
        Returns:
            Notification: The created notification
        """
        # Get recipient email
        users = await self.db_tool.get_user_by_role(recipient_role.value)
        if not users:
            raise ValueError(f"No users found with role {recipient_role}")
        
        # Create notifications for all users with the role
        notifications = []
        for user in users:
            notification_data = {
                "lease_exit_id": lease_exit_id,
                "recipient_role": recipient_role,
                "recipient_email": user.email,
                "subject": subject,
                "message": message,
                "notification_type": notification_type,
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            
            # Create notification record
            notification = await self.notification_tool.create_notification(notification_data)
            
            # Send the email notification
            try:
                await self.notification_tool.send_email_notification(
                    user.email,
                    subject,
                    message
                )
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
            except Exception as e:
                notification.status = "failed"
                print(f"Failed to send notification: {str(e)}")
            
            notifications.append(notification)
        
        return notifications[0] if notifications else None
    
    async def notify_workflow_update(self, lease_exit_id: str, update_type: str) -> List[Notification]:
        """Send notifications about a workflow update
        
        Args:
            lease_exit_id: The ID of the lease exit
            update_type: The type of update
            
        Returns:
            List[Notification]: The created notifications
        """
        # Get the lease exit
        lease_exit = await self.db_tool.get_lease_exit(lease_exit_id)
        if not lease_exit:
            raise ValueError(f"Lease exit with ID {lease_exit_id} not found")
        
        property_address = lease_exit.property_details.get("property_address", "N/A")
        
        # Determine recipients and message based on update type
        recipients = []
        subject = ""
        message = ""
        
        if update_type == "initial_submission":
            recipients = [StakeholderRole.ADVISORY, StakeholderRole.IFM, StakeholderRole.LEGAL]
            subject = f"New Lease Exit Submission - {property_address}"
            message = f"""
            <p>A new lease exit has been submitted for {property_address}.</p>
            <p><strong>Lease Exit ID:</strong> {lease_exit_id}</p>
            <p>Please review the details and complete your required forms.</p>
            <p>You can access the lease exit at: /lease-exits/{lease_exit_id}</p>
            """
        
        elif update_type == "advisory_review_complete":
            recipients = [StakeholderRole.LEGAL, StakeholderRole.IFM, StakeholderRole.ACCOUNTING]
            subject = f"Advisory Review Complete - {property_address}"
            message = f"""
            <p>The Advisory team has completed their review for lease exit at {property_address}.</p>
            <p><strong>Lease Exit ID:</strong> {lease_exit_id}</p>
            <p>Please review the updated information and proceed with your required actions.</p>
            <p>You can access the lease exit at: /lease-exits/{lease_exit_id}</p>
            """
        
        elif update_type == "ifm_review_complete":
            recipients = [StakeholderRole.MAC]
            subject = f"IFM Review Complete - {property_address}"
            message = f"""
            <p>The IFM team has completed their review for lease exit at {property_address}.</p>
            <p><strong>Lease Exit ID:</strong> {lease_exit_id}</p>
            <p>Please review and complete your required forms.</p>
            <p>You can access the lease exit at: /lease-exits/{lease_exit_id}</p>
            """
        
        elif update_type == "mac_review_complete":
            recipients = [StakeholderRole.PJM]
            subject = f"MAC Review Complete - {property_address}"
            message = f"""
            <p>The MAC team has completed their review for lease exit at {property_address}.</p>
            <p><strong>Lease Exit ID:</strong> {lease_exit_id}</p>
            <p>Please review and complete your required forms.</p>
            <p>You can access the lease exit at: /lease-exits/{lease_exit_id}</p>
            """
        
        elif update_type == "pjm_review_complete":
            recipients = [StakeholderRole.LEASE_EXIT_MANAGEMENT]
            subject = f"All Reviews Complete - {property_address}"
            message = f"""
            <p>All teams have completed their reviews for lease exit at {property_address}.</p>
            <p><strong>Lease Exit ID:</strong> {lease_exit_id}</p>
            <p>Please review all details and update the lease exit status as needed.</p>
            <p>You can access the lease exit at: /lease-exits/{lease_exit_id}</p>
            """
        
        elif update_type == "approval_required":
            # For this update, we'll need to get the recipients from the approval chain
            recipients = [step.role for step in lease_exit.approval_chain if step.status == "pending"]
            subject = f"Approval Required - {property_address}"
            message = f"""
            <p>Your approval is required for the lease exit at {property_address}.</p>
            <p><strong>Lease Exit ID:</strong> {lease_exit_id}</p>
            <p>Please review the details and provide your approval decision.</p>
            <p>You can access the lease exit at: /lease-exits/{lease_exit_id}</p>
            """
        
        elif update_type == "ready_for_exit":
            recipients = [role for role in StakeholderRole]  # Notify all stakeholders
            subject = f"Lease Exit Ready - {property_address}"
            message = f"""
            <p>The lease exit process for {property_address} is now ready for execution.</p>
            <p><strong>Lease Exit ID:</strong> {lease_exit_id}</p>
            <p>All approvals have been received.</p>
            <p>You can access the lease exit details at: /lease-exits/{lease_exit_id}</p>
            """
        
        # Send notifications to all recipients
        notifications = []
        for recipient in recipients:
            notification = await self.create_notification(
                lease_exit_id,
                recipient,
                subject,
                message,
                notification_type="workflow_update"
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    async def resend_failed_notifications(self) -> Dict[str, Any]:
        """Resend failed notifications
        
        Returns:
            Dict: Results of the operation
        """
        client = self.notification_tool.client
        db = client.lease_exit_system
        
        # Find all failed notifications
        cursor = db.notifications.find({"status": "failed"})
        failed_notifications = []
        async for doc in cursor:
            failed_notifications.append(doc)
        
        # Attempt to resend each notification
        resent_count = 0
        still_failed = 0
        
        for notification in failed_notifications:
            try:
                await self.notification_tool.send_email_notification(
                    notification["recipient_email"],
                    notification["subject"],
                    notification["message"]
                )
                
                # Update the notification status
                await db.notifications.update_one(
                    {"_id": notification["_id"]},
                    {
                        "$set": {
                            "status": "sent",
                            "sent_at": datetime.utcnow()
                        }
                    }
                )
                
                resent_count += 1
            except Exception:
                still_failed += 1
        
        return {
            "total_failed": len(failed_notifications),
            "resent_successfully": resent_count,
            "still_failed": still_failed
        }
