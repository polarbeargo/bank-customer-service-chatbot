"""
Security utilities for the chatbot.
Handles sensitive data protection and validation.
"""

import re
from typing import Optional, Set

SENSITIVE_PATTERNS = [
    r'password',
    r'pin',
    r'secret',
    r'token',
    r'credential'
]

FORBIDDEN_KEYWORDS = [
    'password',
    'pwd',
    'pin',
    'secret',
    'api_key',
    'token'
]


class SecurityValidator:
    """Validates responses for security violations."""
    
    @staticmethod
    def contains_sensitive_data(text: str) -> bool:
        """Check if text contains forbidden sensitive keywords."""
        text_lower = text.lower()
        for keyword in FORBIDDEN_KEYWORDS:
            if keyword in text_lower:
                return True
        return False
    
    @staticmethod
    def validate_response(response: str) -> tuple[bool, Optional[str]]:
        """
        Validate response for security issues.
        Returns: (is_valid, error_message)
        """
        if SecurityValidator.contains_sensitive_data(response):
            return False, "Response contains forbidden sensitive information"
        
        return True, None
    
    @staticmethod
    def sanitize_response(response: str) -> str:
        """Remove any sensitive patterns from response."""
        sanitized = response
        for keyword in FORBIDDEN_KEYWORDS:
            sanitized = re.sub(
                rf'\b{keyword}\b',
                '[REDACTED]',
                sanitized,
                flags=re.IGNORECASE
            )
        return sanitized


class InputValidator:
    """Validates user input for injection attacks and malicious content."""
    
    @staticmethod
    def validate_id_number(id_number: str) -> bool:
        """Validate Taiwan ID number format."""
        # Taiwan ID: 1 letter + 9 digits
        return bool(re.match(r'^[A-Z]\d{9}$', id_number.upper()))
    
    @staticmethod
    def validate_dob(dob: str) -> bool:
        """Validate date of birth format (YYYY/MM/DD)."""
        return bool(re.match(r'^\d{4}/\d{2}/\d{2}$', dob))
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate name (basic validation)."""
        if len(name) < 2:
            return False

        dangerous_patterns = ['DROP', 'DELETE', '--', ';', '/*', '*/', 'INSERT', 'UPDATE']
        for pattern in dangerous_patterns:
            if pattern.upper() in name.upper():
                return False
        return True
    
    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """Sanitize user input by removing leading/trailing whitespace."""
        return user_input.strip()
