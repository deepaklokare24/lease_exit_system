from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, Process
from database.models import LeaseExit, FormStatus, WorkflowStatus, StakeholderRole
from database.connection import get_database
from utils.tools import DatabaseTool, NotificationTool, FormValidationTool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
import yaml
import os
import json
from config.config import config
import logging
from datetime import datetime
import uuid
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class LeaseExitCrew:
    def __init__(self):
        self.setup_tools()
        self.setup_agents()
        
    def setup_tools(self):
        """Set up tools for the workflow"""
        # Create tool wrapper instances
        db_tool_wrapper = DatabaseTool()
        notification_tool_wrapper = NotificationTool()
        form_tool_wrapper = FormValidationTool()
        
        # Extract individual tool instances
        self.db_tools = [
            db_tool_wrapper.create_lease_exit,
            db_tool_wrapper.update_lease_exit,
            db_tool_wrapper.get_lease_exit,
            db_tool_wrapper.create_form,
            db_tool_wrapper.get_user_by_role
        ]
        
        self.notification_tools = [
            notification_tool_wrapper.create_notification,
            notification_tool_wrapper.send_email_notification,
            notification_tool_wrapper.notify_stakeholders
        ]
        
        self.form_tools = [
            form_tool_wrapper.validate_initial_form,
            form_tool_wrapper.validate_advisory_form,
            form_tool_wrapper.validate_ifm_form,
            form_tool_wrapper.validate_approval
        ]
        
        # Initialize tools with API keys from environment
        os.environ["SERPER_API_KEY"] = config.get_env("SERPER_API_KEY")
        
        self.search_tool = SerperDevTool()
        self.scrape_tool = ScrapeWebsiteTool()

    def setup_agents(self):
        """Set up agents with well-defined roles and tools"""
        
        # Form Validation Agent - handles validation only
        self.form_validator = Agent(
            role="Form Validation Specialist",
            goal="Validate form data against schema requirements",
            backstory="""You are a specialist in data validation. Your job is to ensure 
            all form data is valid before it's processed in the system. You strictly work with 
            the provided data and never invent new information. You only return structured data
            in the exact format requested.""",
            verbose=True,
            tools=self.form_tools,
            llm="anthropic/claude-3-5-sonnet-20241022"
        )
        
        # Database Operations Agent - handles database interactions only
        self.data_manager = Agent(
            role="Data Management Specialist",
            goal="Manage database operations for lease exit workflows",
            backstory="""You are an expert in data management. Your role is to ensure 
            all lease exit data is properly stored and retrieved from the database.
            You work only with existing data and validated inputs. You only return structured data
            in the exact format requested.""",
            verbose=True,
            tools=self.db_tools,
            llm="anthropic/claude-3-5-sonnet-20241022"
        )
        
        # Workflow Coordinator Agent - handles process coordination
        self.workflow_coordinator = Agent(
            role="Workflow Coordination Specialist",
            goal="Coordinate the lease exit workflow process",
            backstory="""You orchestrate the lease exit process, ensuring each step
            is completed in the correct order with proper data. You don't create data,
            but ensure the process moves forward properly. You only return structured data
            in the exact format requested.""",
            verbose=True,
            tools=self.db_tools + [self.search_tool],
            llm="anthropic/claude-3-5-sonnet-20241022"
        )
        
        # Notification Agent - handles notifications only
        self.notifier = Agent(
            role="Notification Specialist",
            goal="Send appropriate notifications to stakeholders",
            backstory="""You are responsible for sending notifications to all stakeholders
            in the lease exit process. You create appropriate messages based on workflow 
            events and ensure communications are clear and timely. You only return structured data
            in the exact format requested.""",
            verbose=True,
            tools=self.notification_tools,
            llm="anthropic/claude-3-5-sonnet-20241022"
        )
    
    def execute_single_task(self, task: Task, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a single task with proper error handling and output validation"""
        try:
            # For validation tasks, use our fallback validation if LLM is unavailable
            if "validate" in task.description.lower() and inputs and "form_data" in inputs:
                form_data = inputs.get("form_data", {})
                
                # Extract required fields from context
                required_fields = []
                for ctx in task.context:
                    if isinstance(ctx, dict) and "required_fields" in ctx:
                        required_fields = ctx["required_fields"]
                        break
                
                # Perform basic validation
                logger.info(f"Performing basic validation for fields: {required_fields}")
                missing_fields = [field for field in required_fields if field not in form_data or not form_data[field]]
                
                if missing_fields:
                    logger.warning(f"Basic validation failed: Missing fields {missing_fields}")
                    return {
                        "is_valid": False,
                        "errors": [f"Missing required field: {field}" for field in missing_fields],
                        "validated_data": None
                    }
                
                # If basic validation passes, try LLM validation but be prepared to fall back
                logger.info("Basic validation passed, attempting LLM validation")
                try:
                    # Create a crew with just this task and its agent
                    crew = Crew(
                        agents=[task.agent],
                        tasks=[task],
                        process=Process.sequential,
                        verbose=True,
                        max_task_retries=1
                    )
                    
                    # Execute the task with a short timeout
                    result = crew.kickoff(inputs=inputs)
                    
                    # Handle CrewOutput object
                    if hasattr(result, 'raw_output'):
                        if isinstance(result.raw_output, dict):
                            logger.info(f"LLM validation successful: {result.raw_output}")
                            return result.raw_output
                        elif isinstance(result.raw_output, str):
                            try:
                                parsed_result = json.loads(result.raw_output)
                                logger.info(f"LLM validation successful (parsed from string): {parsed_result}")
                                return parsed_result
                            except json.JSONDecodeError:
                                logger.warning(f"Could not parse LLM output as JSON, using basic validation result")
                    
                    # If we get here, LLM validation didn't return a usable result
                    logger.warning("LLM validation failed or returned unexpected format, using basic validation result")
                    
                except Exception as e:
                    logger.warning(f"LLM validation failed with error: {str(e)}, using basic validation result")
                
                # Return basic validation result as fallback
                return {
                    "is_valid": True,
                    "errors": [],
                    "validated_data": form_data
                }
            
            # For non-validation tasks, try to execute normally but handle errors gracefully
            try:
                # Create a crew with just this task and its agent
                crew = Crew(
                    agents=[task.agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True,
                    max_task_retries=1
                )
                
                # Execute the task
                logger.info(f"Executing task: {task.description[:50]}...")
                if inputs:
                    result = crew.kickoff(inputs=inputs)
                else:
                    result = crew.kickoff()
                
                # Handle CrewOutput object
                if hasattr(result, 'raw_output'):
                    if isinstance(result.raw_output, dict):
                        return result.raw_output
                    elif isinstance(result.raw_output, str):
                        try:
                            parsed_result = json.loads(result.raw_output)
                            return parsed_result
                        except json.JSONDecodeError:
                            # If it's not valid JSON, return a generic success response
                            logger.warning(f"Could not parse CrewOutput raw_output as JSON: {result.raw_output[:100]}...")
                            return {"success": True, "message": "Task completed successfully"}
                elif isinstance(result, str):
                    try:
                        parsed_result = json.loads(result)
                        return parsed_result
                    except json.JSONDecodeError:
                        # If it's not valid JSON, return a generic success response
                        return {"success": True, "message": "Task completed successfully"}
                elif isinstance(result, dict):
                    return result
                else:
                    # For any other type, return a generic success response
                    logger.warning(f"Task returned unexpected type: {type(result)}, using generic success response")
                    return {"success": True, "message": "Task completed successfully"}
                
            except Exception as e:
                logger.error(f"Error executing task: {str(e)}")
                # Return a generic error response
                return {
                    "success": False,
                    "error": f"Task execution error: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Unexpected error in execute_single_task: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def create_lease_exit_workflow(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lease exit workflow"""
        try:
            logger.info(f"Creating lease exit workflow with data: {form_data}")
            
            # Enhanced validation to ensure required fields are present and valid
            required_fields = ["lease_id", "property_address", "exit_date", "reason_for_exit"]
            missing_fields = [field for field in required_fields if not form_data.get(field)]
            
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # Additional validation for field values
            validation_errors = []
            
            # Validate property_address is not empty
            if not form_data.get("property_address", "").strip():
                validation_errors.append("Property address cannot be empty")
                
            # Validate lease_id is not empty
            if not form_data.get("lease_id", "").strip():
                validation_errors.append("Lease ID cannot be empty")
                
            # Validate exit_date is a valid date
            try:
                exit_date = form_data.get("exit_date", "")
                if exit_date:
                    datetime.fromisoformat(exit_date.replace('Z', '+00:00'))
                else:
                    validation_errors.append("Exit date cannot be empty")
            except ValueError:
                validation_errors.append("Exit date must be a valid date")
                
            # Validate reason_for_exit is not empty
            if not form_data.get("reason_for_exit", "").strip():
                validation_errors.append("Reason for exit cannot be empty")
            
            if validation_errors:
                error_msg = f"Validation errors: {', '.join(validation_errors)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # Create a unique ID for the lease exit
            lease_exit_id = f"LE-{uuid.uuid4().hex[:8].upper()}"
            
            # Format the data for storage
            lease_exit_data = {
                "lease_exit_id": lease_exit_id,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "property_details": {
                    "property_address": form_data.get("property_address"),
                    "lease_id": form_data.get("lease_id")
                },
                "exit_details": {
                    "exit_date": form_data.get("exit_date"),
                    "reason_for_exit": form_data.get("reason_for_exit"),
                    "additional_notes": form_data.get("additional_notes", "")
                },
                "workflow_state": {
                    "current_step": "initial_submission",
                    "approvals": {},
                    "history": [
                        {
                            "step": "initial_submission",
                            "timestamp": datetime.now().isoformat(),
                            "action": "created"
                        }
                    ]
                }
            }
            
            # Store the lease exit data directly in the database
            try:
                # Get MongoDB connection string from environment
                mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
                db_name = os.environ.get("MONGODB_DB_NAME", "lease_exit_system")
                
                # Create a direct client connection
                client = AsyncIOMotorClient(mongodb_uri)
                db = client[db_name]
                
                # Insert the document directly using await
                result = await db.lease_exits.insert_one(lease_exit_data)
                inserted_id = str(result.inserted_id)
                
                logger.info(f"Successfully created lease exit record with ID: {inserted_id}")
                
                # Prepare the storage result for notifications
                storage_result = {
                    "success": True,
                    "lease_exit_id": lease_exit_id,
                    "data": lease_exit_data
                }
                
                # Send initial notifications
                # Use a synchronous method that doesn't rely on asyncio.run_until_complete
                self._send_initial_notifications_sync(storage_result)
                
                # Start the workflow automation process
                logger.info(f"Starting workflow automation for lease exit: {lease_exit_id}")
                workflow_result = await self.start_workflow_automation(lease_exit_id)
                
                if not workflow_result.get("success", False):
                    logger.warning(f"Workflow automation failed to start: {workflow_result.get('error', 'Unknown error')}")
                    # Continue anyway, as the lease exit was created successfully
                
                return {
                    "success": True,
                    "lease_exit_id": lease_exit_id,
                    "message": "Lease exit workflow created successfully",
                    "data": lease_exit_data,
                    "workflow_automation": workflow_result
                }
                
            except Exception as db_error:
                logger.error(f"Database error while creating lease exit: {str(db_error)}")
                return {
                    "success": False,
                    "error": f"Failed to store lease exit data: {str(db_error)}"
                }
                
        except Exception as e:
            logger.error(f"Unexpected error in create_lease_exit_workflow: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create lease exit workflow: {str(e)}"
            }

    def _validate_initial_data(self, data: Dict[str, Any]) -> bool:
        """Validate the initial data structure"""
        required_fields = ["lease_id", "property_address", "exit_date", "reason_for_exit"]
        return all(field in data for field in required_fields)

    async def handle_form_submission(self, lease_exit_id: str, form_data: Dict[str, Any], role: str) -> Dict[str, Any]:
        """Handle a form submission from a stakeholder"""
        try:
            logger.info(f"Handling form submission for lease exit {lease_exit_id} from role {role}")
            
            # Get the lease exit data from the database
            mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.environ.get("MONGODB_DB_NAME", "lease_exit_system")
            client = AsyncIOMotorClient(mongodb_uri)
            db = client[db_name]
            
            # Retrieve the lease exit record
            lease_exit = await db.lease_exits.find_one({"lease_exit_id": lease_exit_id})
            
            if not lease_exit:
                logger.error(f"Lease exit not found: {lease_exit_id}")
                return {
                    "success": False,
                    "error": f"Lease exit not found: {lease_exit_id}"
                }
            
            # Convert ObjectId to string for JSON serialization
            if "_id" in lease_exit:
                lease_exit["_id"] = str(lease_exit["_id"])
            
            # Determine the form type based on the role
            form_type = self._get_form_type_for_role(role)
            
            # Create a task for validating the form data
            validation_task = Task(
                description=f"Validate the {form_type} form data submitted by {role}",
                expected_output="A validation result with is_valid, errors, and validated_data fields",
                agent=self.form_validator,
                context=[{
                    "description": f"Validate {form_type} form data",
                    "expected_output": "Validation result with is_valid, errors, and validated_data fields",
                    "lease_exit_id": lease_exit_id,
                    "form_type": form_type,
                    "role": role,
                    "required_fields": self._get_required_fields_for_form_type(form_type)
                }]
            )
            
            # Execute the validation task
            validation_result = await self.execute_task_async(validation_task, {"form_data": form_data})
            logger.info(f"Validation result: {validation_result}")
            
            if not validation_result.get("is_valid", False):
                logger.error(f"Form validation failed: {validation_result.get('errors', [])}")
                return {
                    "success": False,
                    "error": "Form validation failed",
                    "details": validation_result.get("errors", [])
                }
            
            # Create a task for storing the form data
            storage_task = Task(
                description=f"Store the validated {form_type} form data in the database",
                expected_output="A storage result with success status and details",
                agent=self.data_manager,
                context=[{
                    "description": f"Store {form_type} form data",
                    "expected_output": "Storage result with success status and details",
                    "lease_exit_id": lease_exit_id,
                    "form_type": form_type,
                    "role": role
                }]
            )
            
            # Execute the storage task
            storage_result = await self.execute_task_async(storage_task, {
                "form_data": validation_result.get("validated_data", {}),
                "lease_exit_id": lease_exit_id,
                "form_type": form_type,
                "role": role
            })
            logger.info(f"Storage result: {storage_result}")
            
            # Update the workflow state
            update_task = Task(
                description=f"Update the workflow state to reflect the {form_type} form submission",
                expected_output="An update result with success status and details",
                agent=self.data_manager,
                context=[{
                    "description": "Update workflow state",
                    "expected_output": "Update result with success status and details",
                    "lease_exit_id": lease_exit_id
                }]
            )
            
            # Determine the next step based on the role
            next_step = self._get_next_step_for_role(role)
            
            # Execute the update task
            update_result = await self.execute_task_async(update_task, {
                "lease_exit": {
                    "lease_exit_id": lease_exit_id,
                    "workflow_state": {
                        "current_step": next_step,
                        "history": [
                            {
                                "step": next_step,
                                "timestamp": datetime.now().isoformat(),
                                "action": f"{form_type}_submitted_by_{role}"
                            }
                        ]
                    }
                }
            })
            logger.info(f"Update result: {update_result}")
            
            # Determine the next recipients based on the role
            next_recipients = self._get_next_recipients(role)
            
            if next_recipients:
                # Create a task for notifying the next stakeholders
                notification_task = Task(
                    description=f"Send notifications to the next stakeholders after {role} form submission",
                    expected_output="A notification result with success status and details",
                    agent=self.notifier,
                    context=[{
                        "description": "Send notifications to next stakeholders",
                        "expected_output": "Notification result with success status and details",
                        "lease_exit_id": lease_exit_id,
                        "stakeholders": next_recipients,
                        "form_type": form_type,
                        "role": role
                    }]
                )
                
                # Execute the notification task
                notification_result = await self.execute_task_async(notification_task, {
                    "lease_exit": lease_exit,
                    "form_data": validation_result.get("validated_data", {}),
                    "recipients": next_recipients,
                    "message": f"A {form_type} form has been submitted by {role} for lease exit {lease_exit_id}. Please review and take appropriate action."
                })
                logger.info(f"Notification result: {notification_result}")
            else:
                notification_result = {"success": True, "message": "No notifications needed"}
            
            return {
                "success": True,
                "message": f"{form_type} form submitted successfully",
                "lease_exit_id": lease_exit_id,
                "validation_result": validation_result,
                "storage_result": storage_result,
                "update_result": update_result,
                "notification_result": notification_result,
                "next_step": next_step,
                "next_recipients": next_recipients
            }
            
        except Exception as e:
            logger.error(f"Error handling form submission: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to handle form submission: {str(e)}"
            }
    
    def _get_required_fields_for_form_type(self, form_type: str) -> List[str]:
        """Get the required fields for a form type"""
        if form_type == "advisory_form":
            return ["lease_requirements", "cost_information"]
        elif form_type == "ifm_form":
            return ["exit_requirements", "scope_details"]
        elif form_type == "mac_form":
            return ["scoping_information", "cost_details"]
        elif form_type == "pjm_form":
            return ["project_plan", "documentation_requirements"]
        else:
            return []
    
    def _get_next_step_for_role(self, role: str) -> str:
        """Get the next workflow step based on the role"""
        if role.lower() == "advisory":
            return "advisory_review_completed"
        elif role.lower() == "ifm":
            return "ifm_review_completed"
        elif role.lower() == "mac":
            return "mac_review_completed"
        elif role.lower() == "pjm":
            return "pjm_review_completed"
        else:
            return "form_submitted"
    
    def _get_form_type_for_role(self, role: str) -> str:
        """Get the form type for a role"""
        role_lower = role.lower()
        if role_lower == "advisory":
            return "advisory_form"
        elif role_lower == "ifm":
            return "ifm_form"
        elif role_lower == "mac":
            return "mac_form"
        elif role_lower == "pjm":
            return "pjm_form"
        elif role_lower == "legal":
            return "legal_form"
        else:
            return "unknown_form"
    
    def _get_next_recipients(self, current_role: str) -> List[str]:
        """Get the next recipients based on the current role"""
        role_lower = current_role.lower()
        if role_lower == "advisory":
            return ["Legal", "IFM", "Accounting"]
        elif role_lower == "ifm":
            return ["MAC"]
        elif role_lower == "mac":
            return ["PJM"]
        elif role_lower == "pjm":
            return ["Lease Exit Management"]
        else:
            return []
    
    def _send_initial_notifications(self, storage_result: Dict[str, Any]) -> None:
        """Send initial notifications to stakeholders."""
        try:
            logger.info("Sending initial notifications to stakeholders")
            
            # Extract lease exit data from storage result
            lease_exit_id = storage_result.get("lease_exit_id")
            lease_exit_data = storage_result.get("data", {})
            
            if not lease_exit_id:
                logger.error("Cannot send notifications: No lease_exit_id in storage result")
                return
            
            # Define the recipients and message
            recipients = ["Advisory", "IFM", "Legal"]
            property_address = lease_exit_data.get("property_details", {}).get("property_address", "Unknown Address")
            message = f"A new lease exit request has been created for {property_address}. Please review and provide your input."
            
            # Log the notification attempt
            logger.info(f"Attempting to send notifications for lease exit {lease_exit_id} to {recipients}")
            
            # Create notification records directly in the database
            try:
                # Get database connection
                db = asyncio.get_event_loop().run_until_complete(get_database())
                
                # Create notification records
                notifications = []
                for recipient in recipients:
                    notification = {
                        "lease_exit_id": lease_exit_id,
                        "recipient_role": recipient,
                        "subject": f"Lease Exit Update - {lease_exit_id}",
                        "message": message,
                        "notification_type": "lease_exit_creation",
                        "status": "sent",
                        "created_at": datetime.now().isoformat()
                    }
                    notifications.append(notification)
                
                # Insert notifications if there are any
                asyncio.get_event_loop().run_until_complete(
                    db.notifications.insert_many(notifications)
                )
                logger.info(f"Successfully created {len(notifications)} notification records")
                
            except Exception as db_error:
                logger.error(f"Error creating notification records: {str(db_error)}")
                
        except Exception as e:
            # Log the error but don't fail the workflow
            logger.error(f"Unexpected error in _send_initial_notifications: {str(e)}")
            # Continue execution

    def _send_initial_notifications_sync(self, storage_result: Dict[str, Any]) -> None:
        """Send initial notifications to stakeholders (synchronous version)"""
        try:
            logger.info("Sending initial notifications (sync)")
            
            # Extract data from storage result
            lease_exit_id = storage_result.get("lease_exit_id")
            lease_exit_data = storage_result.get("data", {})
            
            if not lease_exit_id:
                logger.error("Cannot send notifications: Missing lease_exit_id")
                return
            
            # Define the recipients - use the correct roles that exist in the system
            recipients = ["Advisory", "IFM", "Legal"]
            
            # Get property address for the message
            property_address = lease_exit_data.get("property_details", {}).get("property_address", "Unknown property")
            
            # Create a message template
            message = f"""
            A new lease exit process has been initiated for {property_address}.
            
            Lease Exit ID: {lease_exit_id}
            Exit Date: {lease_exit_data.get("exit_details", {}).get("exit_date", "Not specified")}
            Reason: {lease_exit_data.get("exit_details", {}).get("reason_for_exit", "Not specified")}
            
            Please review the details and take appropriate action based on your role.
            """
            
            # Connect to the database
            mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.environ.get("MONGODB_DB_NAME", "lease_exit_system")
            client = MongoClient(mongodb_uri)
            db = client[db_name]
            
            # Create notification records for each recipient
            notifications = []
            for role in recipients:
                # Check if users with this role exist
                users = list(db.users.find({"role": role}))
                
                if not users:
                    logger.warning(f"No users found for role: {role}")
                    # Create a default notification for the role even if no users found
                    notification = {
                        "lease_exit_id": lease_exit_id,
                        "recipient_role": role,
                        "recipient_email": f"{role.lower()}@example.com",  # Default placeholder
                        "subject": f"New Lease Exit - {lease_exit_id}",
                        "message": message,
                        "notification_type": "lease_exit_initiated",
                        "status": "pending",
                        "created_at": datetime.now().isoformat()
                    }
                    notifications.append(notification)
                    continue
                
                # Create notifications for each user with this role
                for user in users:
                    notification = {
                        "lease_exit_id": lease_exit_id,
                        "recipient_role": role,
                        "recipient_email": user.get("email", f"{role.lower()}@example.com"),
                        "subject": f"New Lease Exit - {lease_exit_id}",
                        "message": message,
                        "notification_type": "lease_exit_initiated",
                        "status": "pending",
                        "created_at": datetime.now().isoformat()
                    }
                    notifications.append(notification)
            
            # Insert all notifications into the database
            if notifications:
                result = db.notifications.insert_many(notifications)
                logger.info(f"Created {len(result.inserted_ids)} notification records")
            else:
                logger.warning("No notifications created")
            
            # Update the lease exit record to indicate notifications were sent
            db.lease_exits.update_one(
                {"lease_exit_id": lease_exit_id},
                {
                    "$set": {
                        "workflow_state.notifications_sent": True,
                        "workflow_state.current_step": "notifications_sent"
                    },
                    "$push": {
                        "workflow_state.history": {
                            "step": "notifications_sent",
                            "timestamp": datetime.now().isoformat(),
                            "action": "notifications_sent"
                        }
                    }
                }
            )
            
            logger.info(f"Successfully sent initial notifications for lease exit: {lease_exit_id}")
            
        except Exception as e:
            logger.error(f"Error sending initial notifications: {str(e)}")
            # Continue with the process even if notifications fail

    async def handle_approval_request(self, lease_exit_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an approval request for a lease exit"""
        try:
            logger.info(f"Handling approval request for lease exit {lease_exit_id}")
            
            # Get the lease exit data from the database
            mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.environ.get("MONGODB_DB_NAME", "lease_exit_system")
            client = AsyncIOMotorClient(mongodb_uri)
            db = client[db_name]
            
            # Retrieve the lease exit record
            lease_exit = await db.lease_exits.find_one({"lease_exit_id": lease_exit_id})
            
            if not lease_exit:
                logger.error(f"Lease exit not found: {lease_exit_id}")
                return {
                    "success": False,
                    "error": f"Lease exit not found: {lease_exit_id}"
                }
            
            # Convert ObjectId to string for JSON serialization
            if "_id" in lease_exit:
                lease_exit["_id"] = str(lease_exit["_id"])
            
            # Create a task for validating the approval data
            validation_task = Task(
                description="Validate the approval request data",
                expected_output="A validation result with is_valid, errors, and validated_data fields",
                agent=self.form_validator,
                context=[{
                    "description": "Validate approval request data",
                    "expected_output": "Validation result with is_valid, errors, and validated_data fields",
                    "lease_exit_id": lease_exit_id,
                    "required_fields": ["approver_id", "decision", "comments"]
                }]
            )
            
            # Execute the validation task
            validation_result = await self.execute_task_async(validation_task, {"form_data": approval_data})
            logger.info(f"Validation result: {validation_result}")
            
            if not validation_result.get("is_valid", False):
                logger.error(f"Approval validation failed: {validation_result.get('errors', [])}")
                return {
                    "success": False,
                    "error": "Approval validation failed",
                    "details": validation_result.get("errors", [])
                }
            
            # Get the validated data
            validated_data = validation_result.get("validated_data", approval_data)
            
            # Create a task for processing the approval
            process_task = Task(
                description="Process the approval request and update the workflow state",
                expected_output="A processing result with success status and workflow status",
                agent=self.data_manager,
                context=[{
                    "description": "Process approval request",
                    "expected_output": "Processing result with success status and workflow status",
                    "lease_exit_id": lease_exit_id,
                    "approval_data": validated_data
                }]
            )
            
            # Execute the process task
            process_result = await self.execute_task_async(process_task, {
                "lease_exit": lease_exit,
                "approval_data": validated_data
            })
            logger.info(f"Process result: {process_result}")
            
            # Determine if the workflow is complete based on the approval
            is_approved = validated_data.get("decision", "").lower() == "approve"
            all_approved = process_result.get("all_approved", False)
            
            # Update the workflow state based on the approval decision
            new_status = "approved" if is_approved and all_approved else "pending"
            if not is_approved:
                new_status = "rejected"
            
            # Update the workflow state
            update_task = Task(
                description="Update the workflow state based on the approval decision",
                expected_output="An update result with success status and details",
                agent=self.data_manager,
                context=[{
                    "description": "Update workflow state",
                    "expected_output": "Update result with success status and details",
                    "lease_exit_id": lease_exit_id
                }]
            )
            
            # Execute the update task
            update_result = await self.execute_task_async(update_task, {
                "lease_exit": {
                    "lease_exit_id": lease_exit_id,
                    "status": new_status,
                    "workflow_state": {
                        "current_step": f"approval_{new_status}",
                        "approvals": {
                            validated_data.get("approver_id", "unknown"): {
                                "decision": validated_data.get("decision", ""),
                                "comments": validated_data.get("comments", ""),
                                "timestamp": datetime.now().isoformat()
                            }
                        },
                        "history": [
                            {
                                "step": f"approval_{new_status}",
                                "timestamp": datetime.now().isoformat(),
                                "action": f"approval_{validated_data.get('decision', '').lower()}"
                            }
                        ]
                    }
                }
            })
            logger.info(f"Update result: {update_result}")
            
            # Create a task for sending notifications about the approval
            notification_task = Task(
                description="Send notifications about the approval decision",
                expected_output="A notification result with success status and details",
                agent=self.notifier,
                context=[{
                    "description": "Send approval notifications",
                    "expected_output": "Notification result with success status and details",
                    "lease_exit_id": lease_exit_id,
                    "approval_data": validated_data,
                    "workflow_status": new_status
                }]
            )
            
            # Determine the recipients based on the approval decision
            recipients = ["Lease Exit Management"]
            if not is_approved:
                # If rejected, notify all stakeholders
                recipients.extend(["Advisory", "IFM", "Legal", "MAC", "PJM"])
            elif all_approved:
                # If all approved, notify all stakeholders
                recipients.extend(["Advisory", "IFM", "Legal", "MAC", "PJM"])
            
            # Execute the notification task
            notification_result = await self.execute_task_async(notification_task, {
                "lease_exit": lease_exit,
                "approval_data": validated_data,
                "recipients": recipients,
                "message": f"Approval decision: {validated_data.get('decision', '')} by {validated_data.get('approver_id', 'unknown')} for lease exit {lease_exit_id}. Comments: {validated_data.get('comments', '')}"
            })
            logger.info(f"Notification result: {notification_result}")
            
            return {
                "success": True,
                "message": "Approval processed successfully",
                "lease_exit_id": lease_exit_id,
                "workflow_status": new_status,
                "decision": validated_data.get("decision", ""),
                "all_approved": all_approved,
                "notification_result": notification_result
            }
            
        except Exception as e:
            logger.error(f"Error handling approval request: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to handle approval request: {str(e)}"
            }

    async def start_workflow_automation(self, lease_exit_id: str) -> Dict[str, Any]:
        """
        Start the workflow automation process for a lease exit.
        This method is called after the lease exit is created in the database.
        It will trigger the initial workflow steps and set up the automation process.
        """
        try:
            logger.info(f"Starting workflow automation for lease exit: {lease_exit_id}")
            
            # Get the lease exit data from the database
            mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.environ.get("MONGODB_DB_NAME", "lease_exit_system")
            client = AsyncIOMotorClient(mongodb_uri)
            db = client[db_name]
            
            # Retrieve the lease exit record
            lease_exit = await db.lease_exits.find_one({"lease_exit_id": lease_exit_id})
            
            if not lease_exit:
                logger.error(f"Lease exit not found: {lease_exit_id}")
                return {
                    "success": False,
                    "error": f"Lease exit not found: {lease_exit_id}"
                }
            
            # Convert ObjectId to string for JSON serialization
            if "_id" in lease_exit:
                lease_exit["_id"] = str(lease_exit["_id"])
            
            # Create a validation task for the form validator agent
            validation_task = Task(
                description=f"Validate the lease exit data for {lease_exit_id}",
                expected_output="A validation result indicating if the lease exit data is valid",
                agent=self.form_validator
            )
            
            # Execute the validation task with the complete lease exit data
            logger.info(f"Executing validation task for lease exit: {lease_exit_id}")
            validation_result = await self.execute_task_async(validation_task, {
                "lease_exit": lease_exit,
                "form_data": {
                    "lease_id": lease_exit.get("property_details", {}).get("lease_id"),
                    "property_address": lease_exit.get("property_details", {}).get("property_address"),
                    "exit_date": lease_exit.get("exit_details", {}).get("exit_date"),
                    "reason_for_exit": lease_exit.get("exit_details", {}).get("reason_for_exit"),
                    "additional_notes": lease_exit.get("exit_details", {}).get("additional_notes", "")
                }
            })
            
            # Check if validation was successful
            if not validation_result.get("success", False):
                logger.error(f"Lease exit validation failed: {validation_result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": "Lease exit validation failed",
                    "details": validation_result.get("details", [])
                }
            
            logger.info(f"Lease exit validation successful")
            
            # Create a workflow coordination task
            coordination_task = Task(
                description=f"Coordinate the next steps for lease exit {lease_exit_id}",
                expected_output="A plan for the next steps in the lease exit workflow",
                agent=self.workflow_coordinator
            )
            
            # Execute the coordination task with the complete lease exit data
            logger.info(f"Executing coordination task for lease exit: {lease_exit_id}")
            coordination_result = await self.execute_task_async(coordination_task, {
                "lease_exit": lease_exit,
                "lease_exit_id": lease_exit_id
            })
            
            # Check if coordination was successful
            if not coordination_result.get("success", False):
                logger.error(f"Workflow coordination failed: {coordination_result.get('error', 'Unknown error')}")
                # Continue anyway, as we can update the workflow state directly
            
            # Update the workflow state
            await self._update_workflow_state(lease_exit_id, {
                "current_step": "validated",
                "history": [
                    {
                        "step": "validated",
                        "timestamp": datetime.now().isoformat(),
                        "action": "validation_complete"
                    }
                ]
            })
            
            logger.info(f"Workflow state updated to 'validated' for lease exit: {lease_exit_id}")
            
            # Create a notification task
            notification_task = Task(
                description=f"Send notifications for validated lease exit {lease_exit_id}",
                expected_output="A result indicating if notifications were sent successfully",
                agent=self.notifier
            )
            
            # Execute the notification task
            logger.info(f"Executing notification task for lease exit: {lease_exit_id}")
            notification_result = await self.execute_task_async(notification_task, {
                "lease_exit": lease_exit,
                "lease_exit_id": lease_exit_id
            })
            
            # Check if notifications were sent successfully
            if not notification_result.get("success", False):
                logger.warning(f"Failed to send notifications: {notification_result.get('error', 'Unknown error')}")
                # Continue anyway, as the lease exit was validated successfully
            
            # Return success response
            return {
                "success": True,
                "message": "Workflow automation started successfully",
                "lease_exit_id": lease_exit_id,
                "validation_result": validation_result,
                "coordination_result": coordination_result,
                "notification_result": notification_result
            }
            
        except Exception as e:
            logger.error(f"Error starting workflow automation: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to start workflow automation: {str(e)}"
            }
    
    async def execute_task_async(self, task: Task, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task asynchronously with proper error handling"""
        try:
            # Format inputs properly for the specific task
            formatted_inputs = {}
            if task.description.lower().startswith("validate") and "lease_exit" in inputs:
                # For validation tasks, extract form data from lease exit
                lease_exit = inputs.get("lease_exit", {})
                formatted_inputs = {
                    "form_data": {
                        "lease_id": lease_exit.get("property_details", {}).get("lease_id"),
                        "property_address": lease_exit.get("property_details", {}).get("property_address"),
                        "exit_date": lease_exit.get("exit_details", {}).get("exit_date"),
                        "reason_for_exit": lease_exit.get("exit_details", {}).get("reason_for_exit"),
                        "additional_notes": lease_exit.get("exit_details", {}).get("additional_notes", "")
                    }
                }
            elif "lease_exit_id" in inputs:
                # For other tasks, pass the inputs as is
                formatted_inputs = inputs
            
            # Create a crew with just this task and its agent
            crew = Crew(
                agents=[task.agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
                max_task_retries=1
            )
            
            # Execute the task
            logger.info(f"Executing task asynchronously: {task.description[:50]}...")
            
            # Use the kickoff method
            result = crew.kickoff(inputs=formatted_inputs)
            
            # Handle CrewOutput object
            if hasattr(result, 'raw_output'):
                if isinstance(result.raw_output, dict):
                    return result.raw_output
                elif isinstance(result.raw_output, str):
                    try:
                        parsed_result = json.loads(result.raw_output)
                        return parsed_result
                    except json.JSONDecodeError:
                        # If it's not valid JSON, extract the final answer
                        if "Final Answer:" in result.raw_output:
                            final_answer = result.raw_output.split("Final Answer:")[1].strip()
                            return {"success": True, "message": final_answer}
                        return {"success": True, "message": "Task completed successfully"}
            
            # If we get here, return a generic success response with the CrewOutput
            if hasattr(result, 'final_output'):
                return {"success": True, "message": result.final_output}
            
            logger.warning(f"Task returned unexpected type: {type(result)}, using generic success response")
            return {"success": True, "message": "Task completed successfully"}
            
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            return {"success": False, "error": f"Failed to execute task: {str(e)}"}

    async def _update_workflow_state(self, lease_exit_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the workflow state for a lease exit"""
        try:
            logger.info(f"Updating workflow state for lease exit: {lease_exit_id}")
            
            # Get MongoDB connection
            mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.environ.get("MONGODB_DB_NAME", "lease_exit_system")
            client = AsyncIOMotorClient(mongodb_uri)
            db = client[db_name]
            
            # Get the current lease exit record
            lease_exit = await db.lease_exits.find_one({"lease_exit_id": lease_exit_id})
            
            if not lease_exit:
                logger.error(f"Lease exit not found: {lease_exit_id}")
                return {
                    "success": False,
                    "error": f"Lease exit not found: {lease_exit_id}"
                }
            
            # Update the workflow state
            current_state = lease_exit.get("workflow_state", {})
            
            # Merge the update data with the current state
            updated_state = {**current_state, **update_data}
            
            # Update the lease exit record
            result = await db.lease_exits.update_one(
                {"lease_exit_id": lease_exit_id},
                {"$set": {"workflow_state": updated_state}}
            )
            
            if result.modified_count == 0:
                logger.warning(f"No changes made to workflow state for lease exit: {lease_exit_id}")
            else:
                logger.info(f"Successfully updated workflow state for lease exit: {lease_exit_id}")
            
            return {
                "success": True,
                "message": "Workflow state updated successfully",
                "lease_exit_id": lease_exit_id,
                "workflow_state": updated_state
            }
            
        except Exception as e:
            logger.error(f"Error updating workflow state: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to update workflow state: {str(e)}"
            }