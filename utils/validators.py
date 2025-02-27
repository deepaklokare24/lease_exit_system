from typing import Dict, Any, List
import re
from datetime import datetime

class FormValidator:
    """Form validation utilities"""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate that required fields are present
        
        Args:
            data: The form data
            required_fields: List of required field names
            
        Returns:
            List of error messages or empty list if valid
        """
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"Missing required field: {field}")
        return errors
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate an email address
        
        Args:
            email: The email address to validate
            
        Returns:
            Whether the email is valid
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_date(date_string: str, format_string: str = "%Y-%m-%d") -> bool:
        """Validate a date string
        
        Args:
            date_string: The date string to validate
            format_string: The expected date format
            
        Returns:
            Whether the date is valid
        """
        try:
            datetime.strptime(date_string, format_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_number(value: Any) -> bool:
        """Validate that a value is a number
        
        Args:
            value: The value to validate
            
        Returns:
            Whether the value is a valid number
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_min_length(value: str, min_length: int) -> bool:
        """Validate that a string has a minimum length
        
        Args:
            value: The string to validate
            min_length: The minimum length
            
        Returns:
            Whether the string is valid
        """
        return len(value) >= min_length
    
    @staticmethod
    def validate_max_length(value: str, max_length: int) -> bool:
        """Validate that a string has a maximum length
        
        Args:
            value: The string to validate
            max_length: The maximum length
            
        Returns:
            Whether the string is valid
        """
        return len(value) <= max_length
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate a URL
        
        Args:
            url: The URL to validate
            
        Returns:
            Whether the URL is valid
        """
        pattern = r"^(https?://)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/[\w-]+)*/?(\?\S+)?$"
        return bool(re.match(pattern, url))

class LeaseExitValidator:
    """Validator for lease exit forms"""
    
    @staticmethod
    def validate_initial_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the initial lease exit form
        
        Args:
            form_data: The form data to validate
            
        Returns:
            Validation result
        """
        required_fields = [
            "lease_id",
            "property_address",
            "exit_date",
            "reason_for_exit"
        ]
        
        validator = FormValidator()
        errors = validator.validate_required_fields(form_data, required_fields)
        
        # Validate date format
        if "exit_date" in form_data and not validator.validate_date(form_data["exit_date"]):
            errors.append("Invalid date format for exit_date. Use YYYY-MM-DD")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": form_data if len(errors) == 0 else None
        }
    
    @staticmethod
    def validate_advisory_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the advisory form
        
        Args:
            form_data: The form data to validate
            
        Returns:
            Validation result
        """
        required_fields = [
            "lease_requirements",
            "cost_information",
            "documents"
        ]
        
        validator = FormValidator()
        errors = validator.validate_required_fields(form_data, required_fields)
        
        # Validate documents field is a list
        if "documents" in form_data and not isinstance(form_data["documents"], list):
            errors.append("documents field must be a list")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": form_data if len(errors) == 0 else None
        }
    
    @staticmethod
    def validate_ifm_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the IFM form
        
        Args:
            form_data: The form data to validate
            
        Returns:
            Validation result
        """
        required_fields = [
            "exit_requirements",
            "scope_details",
            "timeline"
        ]
        
        validator = FormValidator()
        errors = validator.validate_required_fields(form_data, required_fields)
        
        # Validate timeline if present
        if "timeline" in form_data and not validator.validate_date(form_data["timeline"]):
            errors.append("Invalid date format for timeline. Use YYYY-MM-DD")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": form_data if len(errors) == 0 else None
        }
    
    @staticmethod
    def validate_mac_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the MAC form
        
        Args:
            form_data: The form data to validate
            
        Returns:
            Validation result
        """
        required_fields = [
            "scope_details",
            "cost_estimate"
        ]
        
        validator = FormValidator()
        errors = validator.validate_required_fields(form_data, required_fields)
        
        # Validate cost_estimate is a number
        if "cost_estimate" in form_data and not validator.validate_number(form_data["cost_estimate"]):
            errors.append("cost_estimate must be a number")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": form_data if len(errors) == 0 else None
        }
    
    @staticmethod
    def validate_pjm_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the PJM form
        
        Args:
            form_data: The form data to validate
            
        Returns:
            Validation result
        """
        required_fields = [
            "scope_details",
            "project_plan",
            "cost_estimate",
            "timeline"
        ]
        
        validator = FormValidator()
        errors = validator.validate_required_fields(form_data, required_fields)
        
        # Validate cost_estimate is a number
        if "cost_estimate" in form_data and not validator.validate_number(form_data["cost_estimate"]):
            errors.append("cost_estimate must be a number")
        
        # Validate timeline if present
        if "timeline" in form_data and not validator.validate_date(form_data["timeline"]):
            errors.append("Invalid date format for timeline. Use YYYY-MM-DD")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": form_data if len(errors) == 0 else None
        }
    
    @staticmethod
    def validate_approval(approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate approval submission
        
        Args:
            approval_data: The approval data to validate
            
        Returns:
            Validation result
        """
        required_fields = [
            "approver_id",
            "decision",
            "comments"
        ]
        
        validator = FormValidator()
        errors = validator.validate_required_fields(approval_data, required_fields)
        
        # Validate decision
        if "decision" in approval_data and approval_data["decision"] not in ["approve", "reject"]:
            errors.append("decision must be either 'approve' or 'reject'")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_data": approval_data if len(errors) == 0 else None
        }
