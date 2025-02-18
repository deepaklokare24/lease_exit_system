from typing import Dict, Any, List, Optional
from crewai import Tool
from database.models import LeaseExit, FormData, Notification, User, WorkflowStatus
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
from datetime import datetime

class DatabaseTool(Tool):
    def __init__(self):
        self.client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        self.db = self.client.lease_exit_system

    async def create_lease_exit(self, data: Dict[str, Any]) -> LeaseExit:
        """Create a new lease exit record in the database"""
        lease_exit = LeaseExit(**data)
        result = await self.db.lease_exits.insert_one(lease_exit.dict())
        lease_exit.id = str(result.inserted_id)
        return lease_exit

    async def update_lease_exit(self, lease_exit: LeaseExit) -> LeaseExit:
        """Update an existing lease exit record"""
        await self.db.lease_exits.update_one(
            {"_id": ObjectId(lease_exit.id)},
            {"$set": lease_exit.dict(exclude={"id"})}
        )
        return lease_exit

    async def get_lease_exit(self, lease_exit_id: str) -> Optional[LeaseExit]:
        """Retrieve a lease exit record by ID"""
        doc = await self.db.lease_exits.find_one({"_id": ObjectId(lease_exit_id)})
        return LeaseExit(**doc) if doc else None

    async def create_form(self, lease_exit_id: str, form_data: Dict[str, Any]) -> FormData:
        """Create a new form submission"""
        form = FormData(**form_data)
        await self.db.lease_exits.update_one(
            {"_id": ObjectId(lease_exit_id)},
            {"$push": {"forms": form.dict()}}
        )
        return form

    async def get_user_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        cursor = self.db.users.find({"role": role})
        users = []
        async for doc in cursor:
            users.append(User(**doc))
        return users

class NotificationTool(Tool):
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL")

    async def create_notification(self, data: Dict[str, Any]) -> Notification:
        """Create a new notification record"""
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        db = client.lease_exit_system
        
        notification = Notification(**data)
        result = await db.notifications.insert_one(notification.dict())
        notification.id = str(result.inserted_id)
        return notification

    async def send_email_notification(self, to_email: str, subject: str, message: str):
        """Send an email notification"""
        msg = MIMEMultipart()
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        async with aiosmtplib.SMTP(
            hostname=self.smtp_host,
            port=self.smtp_port,
            use_tls=True
        ) as smtp:
            await smtp.login(self.smtp_username, self.smtp_password)
            await smtp.send_message(msg)

    async def notify_stakeholders(self, lease_exit_id: str, recipients: List[str], message: str):
        """Notify multiple stakeholders about a lease exit update"""
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        db = client.lease_exit_system
        
        for recipient in recipients:
            users = await db.users.find({"role": recipient}).to_list(length=None)
            for user in users:
                notification = {
                    "lease_exit_id": lease_exit_id,
                    "recipient_role": recipient,
                    "recipient_email": user["email"],
                    "subject": f"Lease Exit Update - {lease_exit_id}",
                    "message": message,
                    "notification_type": "update",
                    "status": "pending"
                }
                await self.create_notification(notification)
                await self.send_email_notification(
                    user["email"],
                    notification["subject"],
                    notification["message"]
                )

class FormValidationTool(Tool):
    def validate_initial_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the initial lease exit form"""
        required_fields = [
            "lease_id",
            "property_address",
            "exit_date",
            "reason_for_exit"
        ]
        
        errors = []
        for field in required_fields:
            if field not in form_data:
                errors.append(f"Missing required field: {field}")
        
        if "exit_date" in form_data:
            try:
                datetime.strptime(form_data["exit_date"], "%Y-%m-%d")
            except ValueError:
                errors.append("Invalid date format for exit_date. Use YYYY-MM-DD")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": form_data if len(errors) == 0 else None
        }

    def validate_advisory_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the advisory form"""
        required_fields = [
            "lease_requirements",
            "cost_information",
            "documents"
        ]
        
        errors = []
        for field in required_fields:
            if field not in form_data:
                errors.append(f"Missing required field: {field}")
        
        if "documents" in form_data and not isinstance(form_data["documents"], list):
            errors.append("documents field must be a list")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": form_data if len(errors) == 0 else None
        }

    def validate_ifm_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the IFM form"""
        required_fields = [
            "exit_requirements",
            "scope_details",
            "timeline"
        ]
        
        errors = []
        for field in required_fields:
            if field not in form_data:
                errors.append(f"Missing required field: {field}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": form_data if len(errors) == 0 else None
        }

    def validate_approval(self, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate approval submission"""
        required_fields = [
            "approver_id",
            "decision",
            "comments"
        ]
        
        errors = []
        for field in required_fields:
            if field not in approval_data:
                errors.append(f"Missing required field: {field}")
        
        if "decision" in approval_data and approval_data["decision"] not in ["approve", "reject"]:
            errors.append("decision must be either 'approve' or 'reject'")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": approval_data if len(errors) == 0 else None
        }