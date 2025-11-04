"""
Input Validation Module
Provides validation functions for common input types
"""

from typing import Any, Union, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class Validator:
    """
    Input validation utility class.
    Provides methods to validate various input types.
    """
    
    @staticmethod
    def validate_speed(speed: Union[int, float], min_speed: int = 0, max_speed: int = 100) -> bool:
        """
        Validate speed value.
        
        Args:
            speed (Union[int, float]): Speed value to validate
            min_speed (int): Minimum allowed speed
            max_speed (int): Maximum allowed speed
        
        Returns:
            bool: True if valid, raises ValidationError otherwise
        
        Raises:
            ValidationError: If speed is invalid
        """
        if not isinstance(speed, (int, float)):
            raise ValidationError(f"Speed must be numeric, got {type(speed)}")
        
        if speed < min_speed or speed > max_speed:
            raise ValidationError(f"Speed {speed} out of range [{min_speed}, {max_speed}]")
        
        return True
    
    @staticmethod
    def validate_distance(distance: Union[int, float], min_dist: float = 0.0) -> bool:
        """
        Validate distance value.
        
        Args:
            distance (Union[int, float]): Distance value to validate
            min_dist (float): Minimum allowed distance
        
        Returns:
            bool: True if valid, raises ValidationError otherwise
        
        Raises:
            ValidationError: If distance is invalid
        """
        if not isinstance(distance, (int, float)):
            raise ValidationError(f"Distance must be numeric, got {type(distance)}")
        
        if distance < min_dist:
            raise ValidationError(f"Distance {distance} cannot be less than {min_dist}")
        
        return True
    
    @staticmethod
    def validate_gpio_pin(pin: int) -> bool:
        """
        Validate GPIO pin number.
        
        Args:
            pin (int): GPIO pin number
        
        Returns:
            bool: True if valid, raises ValidationError otherwise
        
        Raises:
            ValidationError: If pin is invalid
        """
        if not isinstance(pin, int):
            raise ValidationError(f"GPIO pin must be integer, got {type(pin)}")
        
        if pin < 0 or pin > 27:  # Raspberry Pi GPIO range
            raise ValidationError(f"GPIO pin {pin} out of valid range [0, 27]")
        
        return True
    
    @staticmethod
    def validate_confidence(confidence: float) -> bool:
        """
        Validate confidence score (0.0 to 1.0).
        
        Args:
            confidence (float): Confidence score
        
        Returns:
            bool: True if valid, raises ValidationError otherwise
        
        Raises:
            ValidationError: If confidence is invalid
        """
        if not isinstance(confidence, (int, float)):
            raise ValidationError(f"Confidence must be numeric, got {type(confidence)}")
        
        if confidence < 0.0 or confidence > 1.0:
            raise ValidationError(f"Confidence {confidence} out of range [0.0, 1.0]")
        
        return True
    
    @staticmethod
    def validate_string(value: str, min_length: int = 1, max_length: Optional[int] = None) -> bool:
        """
        Validate string value.
        
        Args:
            value (str): String to validate
            min_length (int): Minimum string length
            max_length (Optional[int]): Maximum string length
        
        Returns:
            bool: True if valid, raises ValidationError otherwise
        
        Raises:
            ValidationError: If string is invalid
        """
        if not isinstance(value, str):
            raise ValidationError(f"Value must be string, got {type(value)}")
        
        if len(value) < min_length:
            raise ValidationError(f"String length {len(value)} less than minimum {min_length}")
        
        if max_length and len(value) > max_length:
            raise ValidationError(f"String length {len(value)} exceeds maximum {max_length}")
        
        return True
    
    @staticmethod
    def validate_list(value: List, min_length: int = 0, max_length: Optional[int] = None) -> bool:
        """
        Validate list value.
        
        Args:
            value (List): List to validate
            min_length (int): Minimum list length
            max_length (Optional[int]): Maximum list length
        
        Returns:
            bool: True if valid, raises ValidationError otherwise
        
        Raises:
            ValidationError: If list is invalid
        """
        if not isinstance(value, list):
            raise ValidationError(f"Value must be list, got {type(value)}")
        
        if len(value) < min_length:
            raise ValidationError(f"List length {len(value)} less than minimum {min_length}")
        
        if max_length and len(value) > max_length:
            raise ValidationError(f"List length {len(value)} exceeds maximum {max_length}")
        
        return True
    
    @staticmethod
    def validate_dict(value: dict, required_keys: Optional[List[str]] = None) -> bool:
        """
        Validate dictionary value.
        
        Args:
            value (dict): Dictionary to validate
            required_keys (Optional[List[str]]): Required keys in dictionary
        
        Returns:
            bool: True if valid, raises ValidationError otherwise
        
        Raises:
            ValidationError: If dictionary is invalid
        """
        if not isinstance(value, dict):
            raise ValidationError(f"Value must be dict, got {type(value)}")
        
        if required_keys:
            missing_keys = set(required_keys) - set(value.keys())
            if missing_keys:
                raise ValidationError(f"Missing required keys: {missing_keys}")
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email (str): Email address to validate
        
        Returns:
            bool: True if valid, raises ValidationError otherwise
        
        Raises:
            ValidationError: If email is invalid
        """
        if not isinstance(email, str):
            raise ValidationError(f"Email must be string, got {type(email)}")
        
        if '@' not in email or '.' not in email:
            raise ValidationError(f"Invalid email format: {email}")
        
        return True

