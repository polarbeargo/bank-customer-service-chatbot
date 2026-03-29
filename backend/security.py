"""
Security utilities for the chatbot.
Handles sensitive data protection and validation.
"""

import re
from typing import Optional, Tuple

FORBIDDEN_KEYWORDS = [
    'password',
    'pwd',
    'pin',
    'secret',
    'api_key',
    'token'
]

PROMPT_LEAKAGE_PATTERNS = [
    r'system\s+prompt',
    r'internal\s+instructions',
    r'hidden\s+instructions',
    r'developer\s+message',
    r'chain\s+of\s+thought'
]

COMPILED_PROMPT_LEAKAGE_PATTERNS: Tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in PROMPT_LEAKAGE_PATTERNS
)


class SecurityValidator:
    """Validates responses for security violations."""
    
    @staticmethod
    def contains_sensitive_data(text: str) -> bool:
        """Check if text contains forbidden sensitive keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in FORBIDDEN_KEYWORDS)

    @staticmethod
    def contains_prompt_leakage(text: str) -> bool:
        """Detect output that looks like prompt or internal policy leakage."""
        return any(pattern.search(text) for pattern in COMPILED_PROMPT_LEAKAGE_PATTERNS)
    
    @staticmethod
    def validate_response(response: str) -> tuple[bool, Optional[str]]:
        """
        Validate response for security issues.
        Returns: (is_valid, error_message)
        """
        if SecurityValidator.contains_sensitive_data(response):
            return False, "Response contains forbidden sensitive information"

        if SecurityValidator.contains_prompt_leakage(response):
            return False, "Response contains potential prompt leakage"
        
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

        if SecurityValidator.contains_prompt_leakage(sanitized):
            return "I can only provide approved banking support information."

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
