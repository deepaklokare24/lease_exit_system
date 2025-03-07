from typing import Dict, Any, List, Optional, Type
from crewai.tools import BaseTool
from database.models import LeaseExit, FormData, Notification, User, WorkflowStatus
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
from datetime import datetime
from pydantic import BaseModel, Field
from config.config import config
import logging
from pymongo import MongoClient

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)  # Convert ObjectId to string
        return super().default(obj)

# Input schemas for tools
class CreateLeaseExitInput(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data for creating a new lease exit record")

class UpdateLeaseExitInput(BaseModel):
    lease_exit: Dict[str, Any] = Field(..., description="Lease exit record to update")

class GetLeaseExitInput(BaseModel):
    lease_exit_id: str = Field(..., description="ID of the lease exit record to retrieve")

class CreateFormInput(BaseModel):
    lease_exit_id: str = Field(..., description="ID of the lease exit record")
    form_data: Dict[str, Any] = Field(..., description="Form data to submit")

class GetUserByRoleInput(BaseModel):
    role: str = Field(..., description="Role to filter users by")

class CreateNotificationInput(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data for creating a new notification")

class SendEmailInput(BaseModel):
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    message: str = Field(..., description="Email message body (HTML)")

class NotifyStakeholdersInput(BaseModel):
    lease_exit_id: str = Field(..., description="ID of the lease exit record")
    recipients: List[str] = Field(..., description="List of recipient roles")
    message: str = Field(..., description="Notification message")

class ValidateFormInput(BaseModel):
    form_data: Dict[str, Any] = Field(..., description="Form data to validate")

class ValidateApprovalInput(BaseModel):
    approval_data: Dict[str, Any] = Field(..., description="Approval data to validate")

# Tool implementations
class CreateLeaseExitTool(BaseTool):
    name: str = "create_lease_exit"
    description: str = "Create a new lease exit record in the database"
    args_schema: Type[BaseModel] = CreateLeaseExitInput
    db_name: str = Field(default="lease_exit_system", description="Database name to use")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.db_name = config.get_db_name()
        
    def _run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper around the async _run method"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._async_run(data))
        
    async def _async_run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lease exit record in the database"""
        # Ensure data is JSON serializable (handle datetime objects)
        json_data = json.loads(json.dumps(data, cls=DateTimeEncoder))
        
        # Create client inside the run method since this is async
        client = AsyncIOMotorClient(config.get_mongodb_uri())
        db = client[self.db_name]
        
        try:
            # Insert into the database
            result = await db.lease_exits.insert_one(json_data)
            
            # Add the ID to the returned data
            json_data["id"] = str(result.inserted_id)
            
            return json_data
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating lease exit: {str(e)}")
            raise e
        finally:
            client.close()

class UpdateLeaseExitTool(BaseTool):
    name: str = "update_lease_exit"
    description: str = "Update an existing lease exit record"
    args_schema: Type[BaseModel] = UpdateLeaseExitInput
    db_name: str = Field(default="lease_exit_system", description="Database name to use")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.db_name = config.get_db_name()
        
    def _run(self, lease_exit: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper around the async _run method"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._async_run(lease_exit))
        
    async def _async_run(self, lease_exit: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing lease exit record"""
        # Ensure data is JSON serializable (handle datetime objects)
        json_data = json.loads(json.dumps(lease_exit, cls=DateTimeEncoder))
        
        # Create client inside the run method since this is async
        client = AsyncIOMotorClient(config.get_mongodb_uri())
        db = client[self.db_name]
        
        try:
            # Extract ID if present
            lease_id = json_data.pop("id", None)
            if not lease_id:
                raise ValueError("Lease exit ID is required for updates")
                
            # Convert string ID to ObjectId
            object_id = ObjectId(lease_id)
            
            # Update the document
            result = await db.lease_exits.update_one(
                {"_id": object_id},
                {"$set": json_data}
            )
            
            if result.matched_count == 0:
                raise ValueError(f"No lease exit found with ID: {lease_id}")
                
            # Return the updated document
            updated_doc = await db.lease_exits.find_one({"_id": object_id})
            if updated_doc:
                updated_doc["id"] = str(updated_doc.pop("_id"))
                return updated_doc
                
            return {"status": "updated", "id": lease_id}
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating lease exit: {str(e)}")
            raise e
        finally:
            client.close()

class GetLeaseExitTool(BaseTool):
    name: str = "get_lease_exit"
    description: str = "Retrieve a lease exit record by ID"
    args_schema: Type[BaseModel] = GetLeaseExitInput
    db_name: str = Field(default="lease_exit_system", description="Database name to use")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.db_name = config.get_db_name()
        
    def _run(self, lease_exit_id: str) -> Optional[Dict[str, Any]]:
        """Use a synchronous approach to avoid asyncio event loop issues"""
        try:
            # Use synchronous MongoDB client
            client = MongoClient(config.get_mongodb_uri())
            db = client[self.db_name]
            
            # Check if we're looking for a sample
            if lease_exit_id.lower() == "sample":
                # Return a sample lease exit if requested
                lease_exit = db.lease_exits.find_one({})
            else:
                # Try to find by lease_exit_id field first
                lease_exit = db.lease_exits.find_one({"lease_exit_id": lease_exit_id})
                
                # If not found, try to find by ObjectId
                if not lease_exit:
                    try:
                        lease_exit = db.lease_exits.find_one({"_id": ObjectId(lease_exit_id)})
                    except Exception:
                        # If not a valid ObjectId, try to find by lease_id
                        lease_exit = db.lease_exits.find_one({"lease_id": lease_exit_id})
            
            # If found, format and return
            if lease_exit:
                if "_id" in lease_exit:
                    lease_exit["_id"] = str(lease_exit["_id"])
                return {"success": True, "data": lease_exit}
            else:
                return {"success": False, "error": f"Lease exit not found: {lease_exit_id}"}
                
        except Exception as e:
            logging.error(f"Error retrieving lease exit: {str(e)}")
            return {"success": False, "error": f"Failed to retrieve lease exit: {str(e)}"}
        
    async def _async_run(self, lease_exit_id: str) -> Optional[Dict[str, Any]]:
        """This method is kept for backward compatibility but not used"""
        return self._run(lease_exit_id)

class CreateFormTool(BaseTool):
    name: str = "create_form"
    description: str = "Create a new form submission"
    args_schema: Type[BaseModel] = CreateFormInput
    db_name: str = Field(default="lease_exit_system", description="Database name to use")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.db_name = config.get_db_name()
        
    def _run(self, lease_exit_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper around the async _run method"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._async_run(lease_exit_id, form_data))
        
    async def _async_run(self, lease_exit_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new form submission for a lease exit"""
        # Ensure data is JSON serializable (handle datetime objects)
        json_data = json.loads(json.dumps(form_data, cls=DateTimeEncoder))
        
        # Add metadata
        json_data["submitted_at"] = datetime.utcnow().isoformat()
        json_data["status"] = "submitted"
        
        # Create client inside the run method since this is async
        client = AsyncIOMotorClient(config.get_mongodb_uri())
        db = client[self.db_name]
        
        try:
            # Get the lease exit document
            lease_exit = await db.lease_exits.find_one({"_id": ObjectId(lease_exit_id)})
            if not lease_exit:
                raise ValueError(f"No lease exit found with ID: {lease_exit_id}")
                
            # Add the form to the lease exit's forms collection
            form_type = json_data.get("form_type", "unknown")
            
            # Update the lease exit document
            update_result = await db.lease_exits.update_one(
                {"_id": ObjectId(lease_exit_id)},
                {
                    "$set": {
                        f"forms.{form_type}": json_data,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )
            
            if update_result.modified_count == 0:
                raise ValueError(f"Failed to update lease exit {lease_exit_id} with form data")
                
            return {
                "lease_exit_id": lease_exit_id,
                "form_type": form_type,
                "status": "submitted",
                "submitted_at": json_data["submitted_at"]
            }
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating form submission: {str(e)}")
            raise e
        finally:
            client.close()

class GetUserByRoleTool(BaseTool):
    name: str = "get_user_by_role"
    description: str = "Get users by role"
    args_schema: Type[BaseModel] = GetUserByRoleInput
    db_name: str = Field(default="lease_exit_system", description="Database name to use")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.db_name = config.get_db_name()
        
    def _run(self, role: str) -> List[Dict[str, Any]]:
        """Synchronous wrapper around the async _run method"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._async_run(role))
        
    async def _async_run(self, role: str) -> List[Dict[str, Any]]:
        """Get users by role"""
        # Create client inside the run method since this is async
        client = AsyncIOMotorClient(config.get_mongodb_uri())
        db = client[self.db_name]
        
        try:
            # Query for users with the given role
            users = await db.users.find({"role": role}).to_list(length=100)
            
            # Format output
            formatted_users = []
            for user in users:
                if "_id" in user:
                    user["id"] = str(user.pop("_id"))
                formatted_users.append(user)
                
            return formatted_users
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting users by role: {str(e)}")
            raise e
        finally:
            client.close()

class CreateNotificationTool(BaseTool):
    name: str = "create_notification"
    description: str = "Create a new notification record"
    args_schema: Type[BaseModel] = CreateNotificationInput
    db_name: str = Field(default="lease_exit_system", description="Database name")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.db_name = config.get_env("MONGODB_DB_NAME", "lease_exit_system")
    
    def _run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper around the async _run method"""
        import asyncio
        
        # Ensure data is properly formatted
        if not isinstance(data, dict):
            logger = logging.getLogger(__name__)
            logger.error(f"Invalid data format: {data}")
            raise ValueError("Data must be a dictionary")
        
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in a running event loop, use synchronous approach
                logger = logging.getLogger(__name__)
                logger.info("Event loop already running, using synchronous approach")
                
                # Connect to MongoDB directly using synchronous client
                client = MongoClient(config.get_mongodb_uri())
                db = client[self.db_name]
                
                try:
                    # Ensure data is JSON serializable
                    json_data = json.loads(json.dumps(data, cls=DateTimeEncoder))
                    
                    # Add timestamp if not present
                    if "created_at" not in json_data:
                        json_data["created_at"] = datetime.utcnow().isoformat()
                        
                    # Insert into database
                    result = db.notifications.insert_one(json_data)
                    
                    # Add ID to response
                    json_data["id"] = str(result.inserted_id)
                    
                    return json_data
                    
                except Exception as e:
                    logger.error(f"Error creating notification: {str(e)}")
                    raise e
                finally:
                    client.close()
            else:
                # If we're not in a running event loop, use run_until_complete
                return loop.run_until_complete(self._async_run(data))
        except RuntimeError:
            # If we can't get the event loop, create a new one
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self._async_run(data))
            finally:
                new_loop.close()

    async def _async_run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new notification record"""
        # Create client inside the run method since this is async
        client = AsyncIOMotorClient(config.get_mongodb_uri())
        db = client[self.db_name]
        
        try:
            # Ensure data is JSON serializable
            json_data = json.loads(json.dumps(data, cls=DateTimeEncoder))
            
            # Add timestamp if not present
            if "created_at" not in json_data:
                json_data["created_at"] = datetime.utcnow().isoformat()
                
            # Insert into database
            result = await db.notifications.insert_one(json_data)
            
            # Add ID to response
            json_data["id"] = str(result.inserted_id)
            
            return json_data
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating notification: {str(e)}")
            raise e
        finally:
            client.close()

class SendEmailTool(BaseTool):
    name: str = "send_email_notification"
    description: str = "Send an email notification"
    args_schema: Type[BaseModel] = SendEmailInput
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    from_email: str = Field(default="", description="From email address")
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # Set up email configuration
        self.smtp_host = config.get_env("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(config.get_env("SMTP_PORT", "587"))
        self.smtp_username = config.get_env("SMTP_USERNAME", "")
        self.smtp_password = config.get_env("SMTP_PASSWORD", "")
        self.from_email = config.get_env("FROM_EMAIL", "")
        
    def _run(self, to_email: str, subject: str, message: str) -> bool:
        """Synchronous wrapper around the async _run method"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._async_run(to_email, subject, message))
        
    async def _async_run(self, to_email: str, subject: str, message: str) -> bool:
        """Send an email notification"""
        try:
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "html"))
            
            # Connect to SMTP server and send
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(self.smtp_username, self.smtp_password)
                await smtp.send_message(msg)
                
            return True
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

class NotifyStakeholdersTool(BaseTool):
    name: str = "notify_stakeholders"
    description: str = "Notify multiple stakeholders about a lease exit update"
    args_schema: Type[BaseModel] = NotifyStakeholdersInput
    db_name: str = Field(default="lease_exit_system", description="Database name to use")
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    from_email: str = Field(default="", description="From email address")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.db_name = config.get_db_name()
        
        # Set up email configuration
        self.smtp_host = config.get_env("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(config.get_env("SMTP_PORT", "587"))
        self.smtp_username = config.get_env("SMTP_USERNAME", "")
        self.smtp_password = config.get_env("SMTP_PASSWORD", "")
        self.from_email = config.get_env("FROM_EMAIL", "")
    
    def _run(self, lease_exit_id: str, recipients: List[str], message: str):
        """Synchronous wrapper around the async _run method"""
        import asyncio
        
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in a running event loop, create a new one
                # or use a synchronous approach
                logger = logging.getLogger(__name__)
                logger.info("Event loop already running, using synchronous approach")
                
                # Connect to MongoDB directly using synchronous client
                client = MongoClient(config.get_mongodb_uri())
                db = client[self.db_name]
                
                results = []
                
                # Process each recipient
                for role in recipients:
                    users = list(db.users.find({"role": role}))
                    
                    if not users:
                        logger.warning(f"No users found for role: {role}")
                        # Create a default notification for the role even if no users found
                        notification = {
                            "lease_exit_id": lease_exit_id,
                            "recipient_role": role,
                            "recipient_email": f"{role}@example.com",  # Default placeholder
                            "subject": f"Lease Exit Update - {lease_exit_id}",
                            "message": message,
                            "notification_type": "lease_exit_update",
                            "status": "pending",
                            "created_at": datetime.utcnow().isoformat()
                        }
                        
                        # Save to database
                        result = db.notifications.insert_one(notification)
                        notification_id = str(result.inserted_id)
                        results.append({
                            "success": True,
                            "notification_id": notification_id,
                            "role": role,
                            "status": "pending"
                        })
                        continue
                    
                    for user in users:
                        # Create notification record
                        notification = {
                            "lease_exit_id": lease_exit_id,
                            "recipient_role": role,
                            "recipient_email": user.get("email", ""),
                            "subject": f"Lease Exit Update - {lease_exit_id}",
                            "message": message,
                            "notification_type": "lease_exit_update",
                            "status": "pending",
                            "created_at": datetime.utcnow().isoformat()
                        }
                        
                        # Save to database
                        result = db.notifications.insert_one(notification)
                        notification_id = str(result.inserted_id)
                        
                        # Add to results
                        results.append({
                            "success": True,
                            "notification_id": notification_id,
                            "role": role,
                            "email": user.get("email", ""),
                            "status": "pending"
                        })
                
                return {
                    "success": True,
                    "message": f"Created {len(results)} notifications",
                    "notifications": results
                }
            else:
                # If we're not in a running event loop, use run_until_complete
                return loop.run_until_complete(self._async_run(lease_exit_id, recipients, message))
        except RuntimeError:
            # If we can't get the event loop, create a new one
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self._async_run(lease_exit_id, recipients, message))
            finally:
                new_loop.close()

    async def _async_run(self, lease_exit_id: str, recipients: List[str], message: str):
        """Create notifications for multiple stakeholders and send emails"""
        # Create client inside the run method since this is async
        client = AsyncIOMotorClient(config.get_mongodb_uri())
        db = client[self.db_name]
        logger = logging.getLogger(__name__)
        
        try:
            results = []
            
            # Get users for each role
            for role in recipients:
                users = await db.users.find({"role": role}).to_list(length=10)
                
                if not users:
                    logger.warning(f"No users found for role: {role}")
                    continue
                
                for user in users:
                    # Create notification record
                    notification = {
                        "lease_exit_id": lease_exit_id,
                        "recipient_role": role,
                        "recipient_email": user.get("email", ""),
                        "subject": f"Lease Exit Update - {lease_exit_id}",
                        "message": message,
                        "notification_type": "lease_exit_update",
                        "status": "pending",
                        "created_at": datetime.utcnow()
                    }
                    
                    # Save to database
                    result = await db.notifications.insert_one(notification)
                    notification_id = str(result.inserted_id)
                    
                    # Send email
                    try:
                        await self._send_email(
                            user.get("email", ""),
                            f"Lease Exit Update - {lease_exit_id}",
                            message
                        )
                        
                        # Update notification status
                        await db.notifications.update_one(
                            {"_id": result.inserted_id},
                            {"$set": {"status": "sent", "sent_at": datetime.utcnow()}}
                        )
                        
                        results.append({
                            "notification_id": notification_id,
                            "recipient": user.get("email", ""),
                            "status": "sent"
                        })
                    except Exception as e:
                        logger.error(f"Failed to send email to {user.get('email', '')}: {str(e)}")
                        results.append({
                            "notification_id": notification_id,
                            "recipient": user.get("email", ""),
                            "status": "failed",
                            "error": str(e)
                        })
            
            return results
        except Exception as e:
            logger.error(f"Error notifying stakeholders: {str(e)}")
            raise e
        finally:
            client.close()

    async def _send_email(self, to_email: str, subject: str, message: str) -> bool:
        """Send an email using SMTP"""
        if not to_email or not subject or not message:
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "html"))
            
            # Connect to SMTP server and send
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(self.smtp_username, self.smtp_password)
                await smtp.send_message(msg)
                
            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

class ValidateInitialFormTool(BaseTool):
    name: str = "validate_initial_form"
    description: str = "Validate the initial lease exit form"
    args_schema: Type[BaseModel] = ValidateFormInput
    
    def _run(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the initial lease exit form"""
        required_fields = ["lease_id", "property_address", "exit_date", "reason_for_exit"]
        
        # Initialize result
        result = {
            "success": True,
            "is_valid": True,
            "errors": [],
            "validated_data": None
        }
        
        # Handle case where form_data might be nested or have different structure
        actual_form_data = form_data
        
        # If form_data is empty or None, check if there's a lease_exit field
        if not actual_form_data and "lease_exit" in form_data:
            # Extract form data from lease_exit
            lease_exit = form_data.get("lease_exit", {})
            actual_form_data = {
                "lease_id": lease_exit.get("property_details", {}).get("lease_id"),
                "property_address": lease_exit.get("property_details", {}).get("property_address"),
                "exit_date": lease_exit.get("exit_details", {}).get("exit_date"),
                "reason_for_exit": lease_exit.get("exit_details", {}).get("reason_for_exit"),
                "additional_notes": lease_exit.get("exit_details", {}).get("additional_notes", "")
            }
        
        # Check for required fields
        for field in required_fields:
            if field not in actual_form_data or not actual_form_data.get(field):
                result["is_valid"] = False
                result["errors"].append(f"Missing required field: {field}")
        
        # Validate field formats if all required fields are present
        if result["is_valid"]:
            # Validate exit_date format
            if "exit_date" in actual_form_data:
                try:
                    # Parse ISO format date string
                    date_obj = datetime.fromisoformat(actual_form_data["exit_date"].replace('Z', '+00:00'))
                    # Ensure it's a future date
                    if date_obj.date() < datetime.now().date():
                        result["is_valid"] = False
                        result["errors"].append("Exit date must be in the future")
                except (ValueError, TypeError):
                    result["is_valid"] = False
                    result["errors"].append("Invalid date format for exit_date. Expected ISO format (YYYY-MM-DD)")
            
            # Add more field validations as needed
            
        # Return validated data if valid
        if result["is_valid"]:
            result["validated_data"] = actual_form_data
            result["message"] = "Form data is valid"
        else:
            result["message"] = f"Form validation failed: {', '.join(result['errors'])}"
            
        return result

class ValidateAdvisoryFormTool(BaseTool):
    name: str = "validate_advisory_form"
    description: str = "Validate the advisory form"
    args_schema: Type[BaseModel] = ValidateFormInput
    
    def _run(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the advisory form"""
        required_fields = ["lease_requirements", "cost_information", "documents"]
        
        # Initialize result
        result = {
            "is_valid": True,
            "errors": [],
            "validated_data": None
        }
        
        # Check for required fields
        for field in required_fields:
            if field not in form_data:
                result["is_valid"] = False
                result["errors"].append(f"Missing required field: {field}")
        
        # Validate field formats if all required fields are present
        if result["is_valid"]:
            # Validate cost_information if present
            if "cost_information" in form_data:
                cost_info = form_data["cost_information"]
                if not isinstance(cost_info, dict):
                    result["is_valid"] = False
                    result["errors"].append("cost_information must be an object")
                else:
                    # Validate numeric fields in cost_information
                    for key, value in cost_info.items():
                        if isinstance(value, (int, float)):
                            if value < 0:
                                result["is_valid"] = False
                                result["errors"].append(f"Cost value '{key}' cannot be negative")
                        elif value is not None and not isinstance(value, str):
                            result["is_valid"] = False
                            result["errors"].append(f"Cost value '{key}' must be a number or string")
            
            # Validate documents if present
            if "documents" in form_data:
                docs = form_data["documents"]
                if not isinstance(docs, dict) and not isinstance(docs, list):
                    result["is_valid"] = False
                    result["errors"].append("documents must be an object or array")
            
            # Add more field validations as needed
            
        # Return validated data if valid
        if result["is_valid"]:
            result["validated_data"] = form_data
            
        return result

class ValidateIFMFormTool(BaseTool):
    name: str = "validate_ifm_form"
    description: str = "Validate the IFM form"
    args_schema: Type[BaseModel] = ValidateFormInput
    
    def _run(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the IFM form"""
        required_fields = ["exit_requirements", "scope_details", "timeline"]
        
        # Initialize result
        result = {
            "is_valid": True,
            "errors": [],
            "validated_data": None
        }
        
        # Check for required fields
        for field in required_fields:
            if field not in form_data:
                result["is_valid"] = False
                result["errors"].append(f"Missing required field: {field}")
        
        # Validate field formats if all required fields are present
        if result["is_valid"]:
            # Validate timeline if present
            if "timeline" in form_data:
                timeline = form_data["timeline"]
                if not isinstance(timeline, dict):
                    result["is_valid"] = False
                    result["errors"].append("timeline must be an object")
                else:
                    # Validate date fields in timeline
                    date_fields = ["completion_date", "handover_date", "inspection_schedule"]
                    for field in date_fields:
                        if field in timeline:
                            try:
                                # Parse ISO format date string
                                datetime.fromisoformat(timeline[field].replace('Z', '+00:00'))
                            except (ValueError, TypeError, AttributeError):
                                result["is_valid"] = False
                                result["errors"].append(f"Invalid date format for {field}. Expected ISO format (YYYY-MM-DD)")
            
            # Add more field validations as needed
            
        # Return validated data if valid
        if result["is_valid"]:
            result["validated_data"] = form_data
            
        return result

class ValidateApprovalTool(BaseTool):
    name: str = "validate_approval"
    description: str = "Validate approval submission"
    args_schema: Type[BaseModel] = ValidateApprovalInput
    
    def _run(self, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate approval submission"""
        required_fields = ["approver_id", "decision"]
        valid_decisions = ["approve", "reject"]
        
        # Initialize result
        result = {
            "is_valid": True,
            "errors": [],
            "validated_data": None
        }
        
        # Check for required fields
        for field in required_fields:
            if field not in approval_data:
                result["is_valid"] = False
                result["errors"].append(f"Missing required field: {field}")
        
        # Validate decision value
        if "decision" in approval_data:
            decision = approval_data["decision"]
            if decision not in valid_decisions:
                result["is_valid"] = False
                result["errors"].append(f"Invalid decision value. Must be one of: {', '.join(valid_decisions)}")
            
            # If decision is reject, comments are required
            if decision == "reject" and (not approval_data.get("comments") or not approval_data["comments"].strip()):
                result["is_valid"] = False
                result["errors"].append("Comments are required when rejecting")
        
        # Return validated data if valid
        if result["is_valid"]:
            result["validated_data"] = approval_data
            
        return result

# For backward compatibility
class DatabaseTool:
    """Wrapper for database tools"""
    def __init__(self):
        self.create_lease_exit = CreateLeaseExitTool()
        self.update_lease_exit = UpdateLeaseExitTool()
        self.get_lease_exit = GetLeaseExitTool()
        self.create_form = CreateFormTool()
        self.get_user_by_role = GetUserByRoleTool()

class NotificationTool:
    """Wrapper for notification tools"""
    def __init__(self):
        self.create_notification = CreateNotificationTool()
        self.send_email_notification = SendEmailTool()
        self.notify_stakeholders = NotifyStakeholdersTool()

class FormValidationTool:
    """Wrapper for form validation tools"""
    def __init__(self):
        self.validate_initial_form = ValidateInitialFormTool()
        self.validate_advisory_form = ValidateAdvisoryFormTool()
        self.validate_ifm_form = ValidateIFMFormTool()
        self.validate_approval = ValidateApprovalTool()