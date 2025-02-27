from typing import Dict, Any, List, Optional
from crewai import Task
from database.models import FormData, FormStatus, Document
from utils.tools import DatabaseTool, FormValidationTool
from agents.form_creator import FormCreatorAgent
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FormTasks:
    """Tasks for managing forms"""
    
    def __init__(self):
        """Initialize form tasks"""
        self.db_tool = DatabaseTool()
        self.form_tool = FormValidationTool()
        self.form_agent = FormCreatorAgent()
    
    async def create_form_template_task(self, form_type: str, required_fields: List[str],
                                      optional_fields: Optional[List[str]] = None) -> Task:
        """Create a task for creating a form template
        
        Args:
            form_type: The type of form
            required_fields: Required fields for the form
            optional_fields: Optional fields for the form
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Create a form template for {form_type}",
            agent=self.form_agent.get_agent(),
            context={
                "form_type": form_type,
                "required_fields": required_fields,
                "optional_fields": optional_fields or []
            }
        )
    
    async def validate_form_submission_task(self, form_type: str, form_data: Dict[str, Any]) -> Task:
        """Create a task for validating a form submission
        
        Args:
            form_type: The type of form
            form_data: The form data to validate
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Validate {form_type} form submission",
            agent=self.form_agent.get_agent(),
            context={
                "form_type": form_type,
                "form_data": form_data
            }
        )
    
    async def execute_validate_form_submission(self, form_type: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the validation of a form submission
        
        Args:
            form_type: The type of form
            form_data: The form data to validate
            
        Returns:
            Dict: The validation result
        """
        try:
            # Validate the form data
            validation_result = await self.form_agent.validate_form_submission(form_type, form_data)
            
            return validation_result
        
        except Exception as e:
            logger.error(f"Error validating form submission: {str(e)}")
            return {
                "is_valid": False,
                "errors": [f"Error validating form submission: {str(e)}"],
                "validated_data": None
            }
    
    async def submit_form_task(self, lease_exit_id: str, form_type: str, 
                             form_data: Dict[str, Any], submitted_by: str) -> Task:
        """Create a task for submitting a form
        
        Args:
            lease_exit_id: The ID of the lease exit
            form_type: The type of form
            form_data: The form data
            submitted_by: The user submitting the form
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Submit {form_type} form for lease exit {lease_exit_id}",
            agent=self.form_agent.get_agent(),
            context={
                "lease_exit_id": lease_exit_id,
                "form_type": form_type,
                "form_data": form_data,
                "submitted_by": submitted_by
            }
        )
    
    async def execute_submit_form(self, lease_exit_id: str, form_type: str, 
                                form_data: Dict[str, Any], submitted_by: str) -> Dict[str, Any]:
        """Execute the submission of a form
        
        Args:
            lease_exit_id: The ID of the lease exit
            form_type: The type of form
            form_data: The form data
            submitted_by: The user submitting the form
            
        Returns:
            Dict: The submission result
        """
        try:
            # Validate the form data
            validation_result = await self.execute_validate_form_submission(form_type, form_data)
            
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "message": "Form validation failed",
                    "errors": validation_result["errors"]
                }
            
            # Get the lease exit
            lease_exit = await self.db_tool.get_lease_exit(lease_exit_id)
            if not lease_exit:
                logger.error(f"Lease exit {lease_exit_id} not found")
                return {
                    "success": False,
                    "message": f"Lease exit {lease_exit_id} not found"
                }
            
            # Create the form data
            form = FormData(
                form_type=form_type,
                data=validation_result["validated_data"],
                status=FormStatus.SUBMITTED,
                submitted_by=submitted_by,
                submitted_at=datetime.utcnow(),
                documents=[]  # Documents will be added separately
            )
            
            # Add the form to the lease exit
            if not lease_exit.forms:
                lease_exit.forms = {}
            
            lease_exit.forms[form_type] = form
            lease_exit.updated_at = datetime.utcnow()
            
            # Update the lease exit
            await self.db_tool.update_lease_exit(lease_exit)
            
            logger.info(f"Submitted {form_type} form for lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": f"Form {form_type} submitted successfully",
                "form_id": form.id
            }
        
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            return {
                "success": False,
                "message": f"Error submitting form: {str(e)}"
            }
    
    async def upload_document_task(self, lease_exit_id: str, document_data: Dict[str, Any]) -> Task:
        """Create a task for uploading a document
        
        Args:
            lease_exit_id: The ID of the lease exit
            document_data: The document data
            
        Returns:
            Task: The created task
        """
        return Task(
            description=f"Upload document for lease exit {lease_exit_id}",
            agent=self.form_agent.get_agent(),
            context={
                "lease_exit_id": lease_exit_id,
                "document_data": document_data
            }
        )
    
    async def execute_upload_document(self, lease_exit_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the upload of a document
        
        Args:
            lease_exit_id: The ID of the lease exit
            document_data: The document data
            
        Returns:
            Dict: The upload result
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
            
            # Create the document
            document = Document(
                name=document_data.get("name"),
                file_path=document_data.get("file_path"),
                document_type=document_data.get("document_type"),
                uploaded_by=document_data.get("uploaded_by"),
                metadata=document_data.get("metadata", {})
            )
            
            # Add the document to the lease exit
            if not lease_exit.documents:
                lease_exit.documents = []
            
            lease_exit.documents.append(document)
            lease_exit.updated_at = datetime.utcnow()
            
            # If the document is for a specific form, add it to that form as well
            form_type = document_data.get("form_type")
            if form_type and form_type in lease_exit.forms:
                lease_exit.forms[form_type].documents.append(document)
            
            # Update the lease exit
            await self.db_tool.update_lease_exit(lease_exit)
            
            logger.info(f"Uploaded document {document.name} for lease exit {lease_exit_id}")
            
            return {
                "success": True,
                "message": "Document uploaded successfully",
                "document_id": document.id
            }
        
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return {
                "success": False,
                "message": f"Error uploading document: {str(e)}"
            }
