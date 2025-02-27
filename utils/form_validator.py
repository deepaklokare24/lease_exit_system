from typing import Dict, Any, List, Optional, Union
import re
from datetime import datetime

class FormValidator:
    """
    Utility class for validating form submissions against defined validation rules.
    """
    
    def validate(self, form: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate form submission data against the form's validation rules.
        
        Args:
            form: The form definition with validation rules
            data: The submitted form data
            
        Returns:
            Dict with validation results
        """
        if not form or not isinstance(form, dict):
            raise ValueError("Invalid form definition")
            
        if not data or not isinstance(data, dict):
            return {
                "is_valid": False,
                "errors": {"_form": "No form data provided"},
                "warnings": {}
            }
        
        # Get validation rules from form
        validation_rules = form.get("validation_rules", {})
        fields = form.get("fields", [])
        
        # Track errors and warnings
        errors = {}
        warnings = {}
        
        # Check required fields
        for field in fields:
            field_id = field.get("id")
            if not field_id:
                continue
                
            # Check if field is required but missing
            if field.get("required", False) and field_id not in data:
                errors[field_id] = "This field is required"
                continue
                
            # Skip validation for empty optional fields
            if field_id not in data or data[field_id] is None or data[field_id] == "":
                continue
                
            # Apply field-specific validation rules
            field_rules = validation_rules.get(field_id, {})
            field_result = self._validate_field(field_id, data[field_id], field_rules, field)
            
            if field_result.get("errors"):
                errors[field_id] = field_result["errors"]
                
            if field_result.get("warnings"):
                warnings[field_id] = field_result["warnings"]
        
        # Check for extra fields not in the form definition
        form_field_ids = [field.get("id") for field in fields if field.get("id")]
        for field_id in data.keys():
            if field_id not in form_field_ids:
                warnings[field_id] = "This field is not defined in the form"
        
        # Return validation results
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_field(self, field_id: str, value: Any, rules: Dict[str, Any], 
                        field_def: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single field value against its rules."""
        result = {"errors": [], "warnings": []}
        
        # Skip empty values (required check is done separately)
        if value is None or value == "":
            return result
            
        field_type = field_def.get("type", "text")
        
        # Type validation
        type_valid = self._validate_type(value, field_type, rules.get("type"))
        if not type_valid["valid"]:
            result["errors"].append(type_valid["error"])
            
        # Run specific validations based on field type and rules
        if field_type == "text" or field_type == "textarea":
            result = self._merge_results(result, self._validate_text(value, rules))
        elif field_type == "number":
            result = self._merge_results(result, self._validate_number(value, rules))
        elif field_type == "date":
            result = self._merge_results(result, self._validate_date(value, rules))
        elif field_type == "select":
            result = self._merge_results(result, self._validate_select(value, field_def.get("options", []), rules))
            
        # Pattern validation
        if "pattern" in rules and isinstance(value, str):
            pattern = rules["pattern"]
            if not re.match(pattern, value):
                error_msg = rules.get("error_message", f"Value does not match the required pattern")
                result["errors"].append(error_msg)
                
        # Custom validation
        if "custom_validation" in rules and callable(rules["custom_validation"]):
            custom_result = rules["custom_validation"](value)
            if not custom_result["valid"]:
                result["errors"].append(custom_result["error"])
        
        return result
    
    def _validate_type(self, value: Any, field_type: str, type_rule: Optional[str] = None) -> Dict[str, Any]:
        """Validate the type of a field value."""
        if not type_rule:
            type_rule = field_type
            
        result = {"valid": True, "error": None}
        
        if type_rule == "string" or type_rule == "text" or type_rule == "textarea":
            if not isinstance(value, str):
                result["valid"] = False
                result["error"] = "Must be a text value"
        elif type_rule == "number":
            try:
                float(value)
            except (ValueError, TypeError):
                result["valid"] = False
                result["error"] = "Must be a numeric value"
        elif type_rule == "boolean" or type_rule == "checkbox":
            if not isinstance(value, bool) and value not in [0, 1, '0', '1', 'true', 'false', 'True', 'False']:
                result["valid"] = False
                result["error"] = "Must be a boolean value"
        elif type_rule == "date":
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    result["valid"] = False
                    result["error"] = "Must be a valid date in ISO format"
            else:
                result["valid"] = False
                result["error"] = "Must be a valid date"
                
        return result
    
    def _validate_text(self, value: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate text field rules."""
        result = {"errors": [], "warnings": []}
        
        # Min length
        if "min_length" in rules and len(value) < rules["min_length"]:
            result["errors"].append(f"Must be at least {rules['min_length']} characters")
            
        # Max length
        if "max_length" in rules and len(value) > rules["max_length"]:
            result["errors"].append(f"Must be no more than {rules['max_length']} characters")
            
        # Email format
        if rules.get("email", False) and not self._is_valid_email(value):
            result["errors"].append("Must be a valid email address")
            
        return result
    
    def _validate_number(self, value: Union[int, float, str], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate number field rules."""
        result = {"errors": [], "warnings": []}
        
        try:
            num_value = float(value)
            
            # Min value
            if "min" in rules and num_value < rules["min"]:
                result["errors"].append(f"Must be at least {rules['min']}")
                
            # Max value
            if "max" in rules and num_value > rules["max"]:
                result["errors"].append(f"Must be no more than {rules['max']}")
                
            # Integer only
            if rules.get("integer", False) and int(num_value) != num_value:
                result["errors"].append("Must be a whole number")
                
        except (ValueError, TypeError):
            # Type validation should have caught this
            pass
            
        return result
    
    def _validate_date(self, value: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate date field rules."""
        result = {"errors": [], "warnings": []}
        
        try:
            date_value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Min date
            if "min_date" in rules:
                min_date = datetime.fromisoformat(rules["min_date"].replace('Z', '+00:00'))
                if date_value < min_date:
                    result["errors"].append(f"Date must be on or after {min_date.strftime('%Y-%m-%d')}")
                    
            # Max date
            if "max_date" in rules:
                max_date = datetime.fromisoformat(rules["max_date"].replace('Z', '+00:00'))
                if date_value > max_date:
                    result["errors"].append(f"Date must be on or before {max_date.strftime('%Y-%m-%d')}")
                    
            # Future date
            if rules.get("future", False) and date_value < today:
                result["errors"].append("Date must be in the future")
                
            # Past date
            if rules.get("past", False) and date_value > today:
                result["errors"].append("Date must be in the past")
                
        except ValueError:
            # Type validation should have caught this
            pass
            
        return result
    
    def _validate_select(self, value: Any, options: List[str], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate select field options."""
        result = {"errors": [], "warnings": []}
        
        if options and value not in options:
            result["errors"].append(f"Must be one of the allowed options: {', '.join(options)}")
            
        return result
    
    def _is_valid_email(self, value: str) -> bool:
        """Check if a value is a valid email."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, value) is not None
    
    def _merge_results(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two validation results."""
        return {
            "errors": result1.get("errors", []) + result2.get("errors", []),
            "warnings": result1.get("warnings", []) + result2.get("warnings", [])
        } 