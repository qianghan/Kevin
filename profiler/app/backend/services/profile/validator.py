"""
Validator implementation for the Profile Service.

This module provides concrete implementations of the ProfileValidatorInterface.
"""

from typing import Dict, List, Any, Optional, Set

from ...utils.logging import get_logger
from .interfaces import ProfileValidatorInterface
from .models import Profile

logger = get_logger(__name__)


class BasicProfileValidator(ProfileValidatorInterface):
    """Basic implementation of profile validator."""
    
    def validate_section_data(self, section_id: str, section_data: Dict[str, Any], 
                            validation_rules: Dict[str, Any]) -> List[str]:
        """
        Validate section data against rules.
        
        Args:
            section_id: ID of the section being validated
            section_data: Data to validate
            validation_rules: Rules to validate against
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        if not validation_rules:
            # No validation rules
            return errors
        
        # Get rules for this section
        if section_id not in validation_rules:
            logger.warning(f"No validation rules found for section {section_id}")
            return errors
        
        section_rules = validation_rules[section_id]
        
        # Check required fields
        required_fields = section_rules.get("required_fields", [])
        for field in required_fields:
            if field not in section_data or section_data[field] is None:
                errors.append(f"Required field '{field}' is missing")
        
        # Check field types
        field_types = section_rules.get("field_types", {})
        for field, field_type in field_types.items():
            if field in section_data and section_data[field] is not None:
                value = section_data[field]
                
                # Check type
                if field_type == "string" and not isinstance(value, str):
                    errors.append(f"Field '{field}' must be a string")
                elif field_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be a number")
                elif field_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Field '{field}' must be a boolean")
                elif field_type == "array" and not isinstance(value, list):
                    errors.append(f"Field '{field}' must be an array")
                elif field_type == "object" and not isinstance(value, dict):
                    errors.append(f"Field '{field}' must be an object")
        
        # Check string length
        string_lengths = section_rules.get("string_lengths", {})
        for field, length_rules in string_lengths.items():
            if field in section_data and isinstance(section_data[field], str):
                value = section_data[field]
                
                # Check min length
                min_length = length_rules.get("min")
                if min_length is not None and len(value) < min_length:
                    errors.append(f"Field '{field}' must be at least {min_length} characters")
                
                # Check max length
                max_length = length_rules.get("max")
                if max_length is not None and len(value) > max_length:
                    errors.append(f"Field '{field}' must be at most {max_length} characters")
        
        # Check number ranges
        number_ranges = section_rules.get("number_ranges", {})
        for field, range_rules in number_ranges.items():
            if field in section_data and isinstance(section_data[field], (int, float)):
                value = section_data[field]
                
                # Check min value
                min_value = range_rules.get("min")
                if min_value is not None and value < min_value:
                    errors.append(f"Field '{field}' must be at least {min_value}")
                
                # Check max value
                max_value = range_rules.get("max")
                if max_value is not None and value > max_value:
                    errors.append(f"Field '{field}' must be at most {max_value}")
        
        # Check allowed values
        allowed_values = section_rules.get("allowed_values", {})
        for field, values in allowed_values.items():
            if field in section_data and section_data[field] not in values:
                errors.append(f"Field '{field}' must be one of: {', '.join(str(v) for v in values)}")
        
        # Log validation results
        if errors:
            logger.warning(f"Validation errors for section {section_id}: {errors}")
        else:
            logger.info(f"Section {section_id} passed validation")
        
        return errors
    
    def validate_section_transition(self, profile: Profile, current_section: str, 
                                  target_section: str) -> List[str]:
        """
        Validate if a transition between sections is allowed.
        
        Args:
            profile: Current profile
            current_section: Current section ID
            target_section: Target section ID
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        # Get section dependencies
        dependencies = profile.config.section_dependencies
        
        # Check if target section depends on any sections
        if target_section in dependencies:
            dependent_sections = dependencies[target_section]
            
            # Check if all dependent sections are completed
            for section_id in dependent_sections:
                section = profile.sections.get(section_id)
                if not section or not section.completed:
                    errors.append(f"Section '{target_section}' requires completion of section '{section_id}'")
        
        # Check if target section is in defined sections
        if target_section not in profile.config.sections:
            errors.append(f"Section '{target_section}' is not defined in profile config")
        
        # Log validation results
        if errors:
            logger.warning(f"Section transition validation errors: {errors}")
        else:
            logger.info(f"Section transition from {current_section} to {target_section} is valid")
        
        return errors 