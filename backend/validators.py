"""
Request and response validation middleware.
Implements OWASP REST Security best practices for input/output validation.
"""

from typing import Dict, Any, Tuple, Optional
from functools import wraps
from flask import request, jsonify
import re


class RequestValidator:
    """Validates incoming API requests."""
    
    MAX_MESSAGE_LENGTH = 5000
    MAX_SESSION_ID_LENGTH = 64
    MAX_JSON_SIZE = 10000
    
    SESSION_ID_PATTERN = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
    
    @staticmethod
    def validate_session_id(session_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate session ID format.
        
        Returns:
            (is_valid, error_message)
        """
        if not session_id:
            return False, "Session ID is required"
        
        if not isinstance(session_id, str):
            return False, "Session ID must be a string"
        
        if len(session_id) > RequestValidator.MAX_SESSION_ID_LENGTH:
            return False, "Session ID too long"
        
        if not RequestValidator.SESSION_ID_PATTERN.match(session_id):
            return False, "Invalid session ID format"
        
        return True, None
    
    @staticmethod
    def validate_message(message: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate chat message content.
        
        Returns:
            (is_valid, error_message)
        """
        if not message:
            return False, "Message is required"
        
        if not isinstance(message, str):
            return False, "Message must be a string"
        
        if len(message) > RequestValidator.MAX_MESSAGE_LENGTH:
            return False, f"Message exceeds maximum length of {RequestValidator.MAX_MESSAGE_LENGTH}"
        
        if '\x00' in message:
            return False, "Message contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_json_size(data: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON payload size.
        
        Returns:
            (is_valid, error_message)
        """
        if len(data) > RequestValidator.MAX_JSON_SIZE:
            return False, f"Request body too large (max {RequestValidator.MAX_JSON_SIZE} bytes)"
        
        return True, None


class ResponseValidator:
    """Validates outgoing API responses."""
    
    @staticmethod
    def validate_response_structure(data: Dict[str, Any], required_fields: list) -> Tuple[bool, Optional[str]]:
        """
        Validate that response contains all required fields.
        
        Returns:
            (is_valid, error_message)
        """
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        return True, None
    
    @staticmethod
    def sanitize_error_message(error: str) -> str:
        """
        Sanitize error messages to prevent information leakage.
        Removes file paths, stack traces, and internal details.
        """
        error = re.sub(r'(/[\w./]+|[A-Z]:\\[\w\\/.]+)', '[PATH]', error)
        error = re.sub(r'line \d+', 'line [N]', error, flags=re.IGNORECASE)
        error = re.sub(r'at 0x[0-9a-f]+', 'at [ADDRESS]', error, flags=re.IGNORECASE)
        
        if len(error) > 200 or 'Traceback' in error or 'Exception' in error:
            return "An internal error occurred. Please try again later."
        
        return error


def validate_request_body(required_fields: Optional[list] = None):
    """
    Decorator to validate request JSON body.
    
    Args:
        required_fields: List of required field names
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'Content-Type must be application/json'
                }), 400
            
            is_valid, error = RequestValidator.validate_json_size(request.get_data())
            if not is_valid:
                return jsonify({'error': error}), 413
            
            try:
                data = request.get_json()
            except Exception:
                return jsonify({'error': 'Invalid JSON'}), 400
            
            if required_fields:
                for field in required_fields:
                    if field not in data:
                        return jsonify({
                            'error': f'Missing required field: {field}'
                        }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_chat_message():
    """
    Decorator to validate chat message in request body.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            message = data.get('message')
            is_valid, error = RequestValidator.validate_message(message)
            if not is_valid:
                return jsonify({'error': error}), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_session_id_param():
    """
    Decorator to validate session_id URL parameter.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(session_id, *args, **kwargs):
            is_valid, error = RequestValidator.validate_session_id(session_id)
            if not is_valid:
                return jsonify({'error': error}), 400
            
            return f(session_id, *args, **kwargs)
        
        return decorated_function
    return decorator
