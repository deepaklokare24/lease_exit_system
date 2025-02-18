from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from database.models import Notification, StakeholderRole
from utils.tools import NotificationTool
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()
notification_tool = NotificationTool()

class NotificationRequest(BaseModel):
    lease_exit_id: str
    recipients: List[StakeholderRole]
    message: str
    notification_type: str = "update"

class NotificationResponse(BaseModel):
    id: str
    lease_exit_id: str
    recipient_role: StakeholderRole
    recipient_email: str
    subject: str
    message: str
    notification_type: str
    status: str
    created_at: str
    sent_at: str = None

@router.post("/notifications", response_model=List[NotificationResponse])
async def send_notifications(request: NotificationRequest):
    """Send notifications to multiple stakeholders"""
    try:
        await notification_tool.notify_stakeholders(
            request.lease_exit_id,
            [role.value for role in request.recipients],
            request.message
        )
        return {"status": "success", "message": "Notifications sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications/{lease_exit_id}", response_model=List[NotificationResponse])
async def get_lease_exit_notifications(lease_exit_id: str):
    """Get all notifications for a specific lease exit"""
    client = notification_tool.client
    db = client.lease_exit_system
    
    cursor = db.notifications.find({"lease_exit_id": lease_exit_id})
    notifications = []
    async for doc in cursor:
        notifications.append(NotificationResponse(**doc))
    return notifications

@router.get("/notifications/role/{role}", response_model=List[NotificationResponse])
async def get_role_notifications(role: StakeholderRole):
    """Get all notifications for a specific role"""
    client = notification_tool.client
    db = client.lease_exit_system
    
    cursor = db.notifications.find({"recipient_role": role.value})
    notifications = []
    async for doc in cursor:
        notifications.append(NotificationResponse(**doc))
    return notifications

@router.post("/notifications/{notification_id}/resend")
async def resend_notification(notification_id: str):
    """Resend a specific notification"""
    client = notification_tool.client
    db = client.lease_exit_system
    
    notification = await db.notifications.find_one({"_id": notification_id})
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    try:
        await notification_tool.send_email_notification(
            notification["recipient_email"],
            notification["subject"],
            notification["message"]
        )
        
        await db.notifications.update_one(
            {"_id": notification_id},
            {
                "$set": {
                    "status": "sent",
                    "sent_at": datetime.utcnow().isoformat()
                }
            }
        )
        return {"status": "success", "message": "Notification resent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
