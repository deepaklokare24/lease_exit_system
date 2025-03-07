from typing import Dict, Any, List, Optional
from crewai import Task
from database.models import StakeholderRole, Notification
from utils.tools import NotificationTool, DatabaseTool
from agents.notification_specialist import NotificationSpecialistAgent
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationTasks:
    """Tasks for managing notifications"""
    
    def __init__(self):
        """Initialize notification tasks"""
        self.notification_tool = NotificationTool()
        self.db_tool = DatabaseTool()
        self.notification_agent = NotificationSpecialistAgent()
    
    async def create_notification_task(self, lease_exit_id: str, recipient_role: StakeholderRole, 
                                     subject: str, message: str) -> Task:
        """Create a task for creating a notification
        
        Args:
            lease_exit_id: The ID of the lease exit
            recipient_role: The role of the recipient
            subject: The notification subject
            message: The notification message
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Create notification for {recipient_role.value} regarding lease exit {lease_exit_id}",
            agent=self.notification_agent.get_agent(),
            context={
                "lease_exit_id": lease_exit_id,
                "recipient_role": recipient_role,
                "subject": subject,
                "message": message
            }
        )
    
    async def execute_create_notification(self, lease_exit_id: str, recipient_role: StakeholderRole, 
                                        subject: str, message: str) -> Dict[str, Any]:
        """Execute the creation of a notification
        
        Args:
            lease_exit_id: The ID of the lease exit
            recipient_role: The role of the recipient
            subject: The notification subject
            message: The notification message
            
        Returns:
            Dict: The execution result
        """
        try:
            notification = await self.notification_agent.create_notification(
                lease_exit_id,
                recipient_role,
                subject,
                message
            )
            
            logger.info(f"Created notification for {recipient_role.value} regarding lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": "Notification created successfully",
                "notification_id": notification.id if notification else None
            }
        
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating notification: {str(e)}"
            }
    
    async def notify_workflow_update_task(self, lease_exit_id: str, update_type: str) -> Task:
        """Create a task for notifying about a workflow update
        
        Args:
            lease_exit_id: The ID of the lease exit
            update_type: The type of update
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Notify stakeholders about {update_type} for lease exit {lease_exit_id}",
            agent=self.notification_agent.get_agent(),
            context={
                "lease_exit_id": lease_exit_id,
                "update_type": update_type
            }
        )
    
    async def execute_notify_workflow_update(self, lease_exit_id: str, update_type: str) -> Dict[str, Any]:
        """Execute the notification of a workflow update
        
        Args:
            lease_exit_id: The ID of the lease exit
            update_type: The type of update
            
        Returns:
            Dict: The execution result
        """
        try:
            notifications = await self.notification_agent.notify_workflow_update(lease_exit_id, update_type)
            
            logger.info(f"Notified stakeholders about {update_type} for lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": f"Stakeholders notified about {update_type}",
                "notification_count": len(notifications)
            }
        
        except Exception as e:
            logger.error(f"Error notifying stakeholders: {str(e)}")
            return {
                "success": False,
                "message": f"Error notifying stakeholders: {str(e)}"
            }
    
    async def notify_multiple_roles_task(self, lease_exit_id: str, roles: List[StakeholderRole], 
                                       subject: str, message: str) -> Task:
        """Create a task for notifying multiple roles
        
        Args:
            lease_exit_id: The ID of the lease exit
            roles: List of roles to notify
            subject: The notification subject
            message: The notification message
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Notify multiple roles about lease exit {lease_exit_id}",
            agent=self.notification_agent.get_agent(),
            context={
                "lease_exit_id": lease_exit_id,
                "roles": roles,
                "subject": subject,
                "message": message
            }
        )
    
    async def execute_notify_multiple_roles(self, lease_exit_id: str, roles: List[StakeholderRole], 
                                          subject: str, message: str) -> Dict[str, Any]:
        """Execute the notification of multiple roles
        
        Args:
            lease_exit_id: The ID of the lease exit
            roles: List of roles to notify
            subject: The notification subject
            message: The notification message
            
        Returns:
            Dict: The execution result
        """
        try:
            notifications = []
            
            for role in roles:
                notification = await self.notification_agent.create_notification(
                    lease_exit_id,
                    role,
                    subject,
                    message
                )
                if notification:
                    notifications.append(notification)
            
            logger.info(f"Notified multiple roles about lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": "Multiple roles notified successfully",
                "notification_count": len(notifications)
            }
        
        except Exception as e:
            logger.error(f"Error notifying multiple roles: {str(e)}")
            return {
                "success": False,
                "message": f"Error notifying multiple roles: {str(e)}"
            }
    
    async def resend_failed_notifications_task(self) -> Task:
        """Create a task for resending failed notifications
        
        Returns:
            Task: The created task
        """
        return Task(
            description="Resend failed notifications",
            agent=self.notification_agent.get_agent(),
            context={}
        )
    
    async def execute_resend_failed_notifications(self) -> Dict[str, Any]:
        """Execute resending of failed notifications
        
        Returns:
            Dict[str, Any]: The execution result
        """
        try:
            # Get all failed notifications
            failed_notifications = await self.db_tool.get_lease_exit.find_notifications(
                {"status": "failed"}
            )
            
            results = []
            for notification in failed_notifications:
                # Attempt to resend the notification
                try:
                    await self.notification_tool.send_email_notification(
                        notification["recipient_email"],
                        notification["subject"],
                        notification["message"]
                    )
                    
                    # Update the notification status
                    notification["status"] = "sent"
                    notification["sent_at"] = datetime.utcnow()
                    await self.db_tool.update_lease_exit.update_notification(
                        notification["id"], 
                        {"status": "sent", "sent_at": datetime.utcnow()}
                    )
                    
                    results.append({
                        "notification_id": notification["id"],
                        "status": "resent"
                    })
                except Exception as e:
                    results.append({
                        "notification_id": notification["id"],
                        "status": "failed",
                        "error": str(e)
                    })
            
            return {
                "status": "completed",
                "message": f"Attempted to resend {len(failed_notifications)} failed notifications",
                "results": results
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error resending failed notifications: {str(e)}"
            }
