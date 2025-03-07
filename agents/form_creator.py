from typing import Dict, Any, List, Optional
from crewai import Agent
from database.models import FormData, LeaseExit
from utils.form_validator import FormValidator
from utils.tools import FormValidationTool as FormTool
from utils.tools import DatabaseTool
import os

class FormCreatorAgent:
    """
    An AI agent responsible for creating, managing, and validating forms within the Lease Exit System.
    This agent analyzes the lease exit context and generates appropriate forms with validation rules.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Form Creator Agent.
        
        Args:
            config: Agent configuration parameters
        """
        self.name = "Form Creator Agent"
        self.description = "Creates and manages dynamic forms based on lease exit context"
        self.form_tool = FormTool()
        self.db_tool = DatabaseTool()
        self.validator = FormValidator()
        
    def get_agent(self) -> Agent:
        """Create and return the Crew AI agent instance
        
        Returns:
            Agent: The Crew AI agent instance
        """
        return Agent(
            role="Form Creation Expert",
            goal="Create intuitive and comprehensive forms for lease exit processes",
            backstory="You are a specialist in form design with experience in real estate documentation and data collection requirements.",
            verbose=True,
            allow_delegation=True,
            tools=[self.form_tool, self.db_tool],
            llm=os.getenv("AI_MODEL", "anthropic/claude-3-5-sonnet-20241022")
        )
    
    async def create_lease_exit_form(self, lease_type: str, property_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a dynamic lease exit initiation form based on lease type and property details.
        
        Args:
            lease_type: The type of lease (commercial, residential, etc.)
            property_details: Details about the property
            
        Returns:
            Form definition and metadata
        """
        # Analyze inputs to determine form requirements
        form_fields = self._determine_form_fields(lease_type, property_details)
        
        # Create form structure
        form = {
            "name": f"{lease_type} Lease Exit Initiation",
            "description": f"Form to initiate the exit process for a {lease_type} lease",
            "fields": form_fields,
            "validation_rules": self._generate_validation_rules(form_fields),
            "lease_type": lease_type,
            "metadata": {
                "property_type": property_details.get("property_type", "unknown"),
                "requires_legal_review": self._requires_legal_review(lease_type, property_details)
            }
        }
        
        # Save the form to database
        form_data = {
            "form_type": "lease_exit_initiation",
            "data": form,
            "status": "active"
        }
        form_id = await self.db_tool.create_form._run(None, form_data)
        form["id"] = form_id
        
        return form
    
    async def customize_form_for_stakeholder(self, form_id: str, stakeholder_role: str) -> Dict[str, Any]:
        """
        Customize an existing form for a specific stakeholder role.
        
        Args:
            form_id: The ID of the base form
            stakeholder_role: The role of the stakeholder
            
        Returns:
            Customized form definition
        """
        # Retrieve the base form
        base_form = await self.db_tool.get_lease_exit.get_form(form_id)
        
        if not base_form:
            raise ValueError(f"Form with ID {form_id} not found")
        
        # Apply role-specific customizations
        customized_fields = self._apply_role_customizations(base_form["fields"], stakeholder_role)
        
        # Create customized form
        customized_form = base_form.copy()
        customized_form["fields"] = customized_fields
        customized_form["name"] = f"{stakeholder_role} - {base_form['name']}"
        customized_form["stakeholder_role"] = stakeholder_role
        
        # Save as a new form
        form_data = {
            "form_type": f"{stakeholder_role}_form",
            "data": customized_form,
            "status": "active"
        }
        new_form_id = await self.db_tool.create_form._run(None, form_data)
        customized_form["id"] = new_form_id
        
        return customized_form
    
    async def validate_form_submission(self, form_id: str, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate form submission data against form rules.
        
        Args:
            form_id: The ID of the form
            submission_data: The data submitted in the form
            
        Returns:
            Validation results with any errors
        """
        # Get the form with its validation rules
        form = await self.db_tool.get_lease_exit.get_form(form_id)
        
        if not form:
            raise ValueError(f"Form with ID {form_id} not found")
        
        # Validate the submission
        validation_result = self.validator.validate(form, submission_data)
        
        # Return validation results
        return {
            "is_valid": validation_result["is_valid"],
            "errors": validation_result.get("errors", {}),
            "warnings": validation_result.get("warnings", {}),
            "form_id": form_id
        }
    
    async def analyze_lease_exit_for_form_requirements(self, lease_exit_id: str) -> List[Dict[str, Any]]:
        """
        Analyze a lease exit to determine what forms are required.
        
        Args:
            lease_exit_id: The ID of the lease exit
            
        Returns:
            List of required forms
        """
        # Get lease exit details
        lease_exit = await self.db_tool.get_lease_exit._run(lease_exit_id)
        
        if not lease_exit:
            raise ValueError(f"Lease exit with ID {lease_exit_id} not found")
        
        # Analyze lease exit to determine required forms
        required_forms = []
        
        # Base initiation form
        required_forms.append({
            "name": "Lease Exit Initiation",
            "required_roles": ["lease_exit_management"],
            "priority": 1
        })
        
        # Determine if advisory review is needed
        if self._needs_advisory_review(lease_exit):
            required_forms.append({
                "name": "Advisory Review",
                "required_roles": ["advisory"],
                "priority": 2
            })
        
        # Determine if IFM review is needed
        if self._needs_ifm_review(lease_exit):
            required_forms.append({
                "name": "IFM Requirements",
                "required_roles": ["ifm"],
                "priority": 2
            })
        
        # Final approval form
        required_forms.append({
            "name": "Final Approval",
            "required_roles": ["approver"],
            "priority": 5
        })
        
        return required_forms
    
    def _determine_form_fields(self, lease_type: str, property_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine the fields needed for a form based on lease type and property details."""
        # Common fields for all lease types
        fields = [
            {
                "id": "lease_id",
                "label": "Lease ID",
                "type": "text",
                "required": True,
                "description": "Unique identifier for the lease"
            },
            {
                "id": "exit_date",
                "label": "Expected Exit Date",
                "type": "date",
                "required": True,
                "description": "The date when the lease exit should be completed"
            },
            {
                "id": "reason",
                "label": "Exit Reason",
                "type": "select",
                "options": ["End of Term", "Early Termination", "Breach of Contract", "Other"],
                "required": True
            }
        ]
        
        # Add lease type specific fields
        if lease_type.lower() == "commercial":
            fields.extend([
                {
                    "id": "square_footage",
                    "label": "Square Footage",
                    "type": "number",
                    "required": True
                },
                {
                    "id": "tenant_improvements",
                    "label": "Tenant Improvements",
                    "type": "textarea",
                    "required": False
                }
            ])
        elif lease_type.lower() == "residential":
            fields.extend([
                {
                    "id": "unit_condition",
                    "label": "Unit Condition",
                    "type": "select",
                    "options": ["Excellent", "Good", "Fair", "Poor"],
                    "required": True
                }
            ])
        
        # Add property type specific fields
        property_type = property_details.get("property_type", "").lower()
        if property_type == "office":
            fields.extend([
                {
                    "id": "floor_number",
                    "label": "Floor Number",
                    "type": "number",
                    "required": True
                }
            ])
        elif property_type == "retail":
            fields.extend([
                {
                    "id": "signage_removal",
                    "label": "Signage Removal Required",
                    "type": "boolean",
                    "required": True
                }
            ])
        
        return fields
    
    def _generate_validation_rules(self, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate validation rules based on form fields."""
        rules = {}
        
        for field in fields:
            field_id = field["id"]
            field_type = field["type"]
            
            # Basic required validation
            if field.get("required", False):
                rules[field_id] = rules.get(field_id, {})
                rules[field_id]["required"] = True
            
            # Type-specific validation
            if field_type == "number":
                rules[field_id] = rules.get(field_id, {})
                rules[field_id]["type"] = "number"
                if field_id == "square_footage":
                    rules[field_id]["min"] = 0
            elif field_type == "date":
                rules[field_id] = rules.get(field_id, {})
                rules[field_id]["type"] = "date"
                if field_id == "exit_date":
                    rules[field_id]["future"] = True
            elif field_type == "text":
                rules[field_id] = rules.get(field_id, {})
                rules[field_id]["type"] = "string"
                if field_id == "lease_id":
                    rules[field_id]["pattern"] = "^[A-Z]{2}-[0-9]{6}$"
                    rules[field_id]["error_message"] = "Lease ID must be in format XX-000000"
            
        return rules
    
    def _requires_legal_review(self, lease_type: str, property_details: Dict[str, Any]) -> bool:
        """Determine if legal review is required based on lease and property details."""
        # Logic to determine if legal review is needed
        if lease_type.lower() == "commercial":
            return True
        
        if property_details.get("value", 0) > 1000000:
            return True
            
        if property_details.get("has_special_conditions", False):
            return True
            
        return False
    
    def _apply_role_customizations(self, fields: List[Dict[str, Any]], stakeholder_role: str) -> List[Dict[str, Any]]:
        """Apply role-specific customizations to form fields."""
        result = fields.copy()
        
        # Add role-specific fields
        if stakeholder_role == "advisory":
            result.extend([
                {
                    "id": "financial_impact",
                    "label": "Financial Impact Assessment",
                    "type": "textarea",
                    "required": True
                },
                {
                    "id": "advisory_recommendation",
                    "label": "Advisory Recommendation",
                    "type": "select",
                    "options": ["Proceed", "Delay", "Renegotiate", "Cancel"],
                    "required": True
                }
            ])
        elif stakeholder_role == "legal":
            result.extend([
                {
                    "id": "legal_risks",
                    "label": "Legal Risks",
                    "type": "textarea",
                    "required": True
                },
                {
                    "id": "contract_obligations",
                    "label": "Outstanding Contractual Obligations",
                    "type": "textarea",
                    "required": True
                }
            ])
        elif stakeholder_role == "ifm":
            result.extend([
                {
                    "id": "required_repairs",
                    "label": "Required Repairs/Maintenance",
                    "type": "textarea",
                    "required": True
                },
                {
                    "id": "estimated_repair_cost",
                    "label": "Estimated Repair Cost",
                    "type": "number",
                    "required": True
                }
            ])
        
        return result
    
    def _needs_advisory_review(self, lease_exit: Dict[str, Any]) -> bool:
        """Determine if this lease exit needs an advisory review."""
        # Logic to determine if advisory review is needed
        if lease_exit.get("early_termination", False):
            return True
            
        if lease_exit.get("financial_impact", 0) > 50000:
            return True
            
        if lease_exit.get("lease_type") == "commercial":
            return True
            
        return False
    
    def _needs_ifm_review(self, lease_exit: Dict[str, Any]) -> bool:
        """Determine if this lease exit needs an IFM review."""
        # Logic to determine if IFM review is needed
        if lease_exit.get("property_type") in ["office", "retail", "warehouse"]:
            return True
            
        if lease_exit.get("has_tenant_improvements", False):
            return True
            
        if lease_exit.get("square_footage", 0) > 5000:
            return True
            
        return False
