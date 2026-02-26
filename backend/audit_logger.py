"""
Audit logging module for security events.
Implements OWASP logging and monitoring requirements.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class AuditEventType(Enum):
    """Types of security audit events."""
    SESSION_CREATED = "session_created"
    SESSION_DELETED = "session_deleted"
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    VERIFICATION_ATTEMPT = "verification_attempt"
    VERIFICATION_SUCCESS = "verification_success"
    VERIFICATION_FAILURE = "verification_failure"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_INPUT = "invalid_input"
    SECURITY_VIOLATION = "security_violation"


class AuditLogger:
    """Handles security audit logging."""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('logs/audit.log')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> None:
        """
        Log a security audit event.
        
        Args:
            event_type: Type of security event
            user_id: Customer/user identifier (redacted)
            session_id: Session identifier (redacted)
            ip_address: Client IP address
            details: Additional event details
            success: Whether the event was successful
        """
        event = {
            "event_type": event_type.value,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            event["user_id"] = self._redact_id(user_id)
        
        if session_id:
            event["session_id"] = self._redact_session(session_id)
        
        if ip_address:
            event["ip_address"] = ip_address
        
        if details:
            event["details"] = details
        
        self.logger.info(json.dumps(event))
    
    def log_verification_attempt(
        self,
        session_id: str,
        ip_address: str,
        success: bool,
        attempts_remaining: Optional[int] = None
    ) -> None:
        """Log identity verification attempt."""
        details = {}
        if attempts_remaining is not None:
            details["attempts_remaining"] = attempts_remaining
        
        event_type = (
            AuditEventType.VERIFICATION_SUCCESS if success
            else AuditEventType.VERIFICATION_FAILURE
        )
        
        self.log_event(
            event_type=event_type,
            session_id=session_id,
            ip_address=ip_address,
            details=details,
            success=success
        )
    
    def log_sensitive_access(
        self,
        user_id: str,
        session_id: str,
        ip_address: str,
        data_type: str
    ) -> None:
        """Log access to sensitive customer data."""
        self.log_event(
            event_type=AuditEventType.SENSITIVE_DATA_ACCESS,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            details={"data_type": data_type},
            success=True
        )
    
    def log_rate_limit(
        self,
        ip_address: str,
        endpoint: str
    ) -> None:
        """Log rate limit violation."""
        self.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            details={"endpoint": endpoint},
            success=False
        )
    
    def log_security_violation(
        self,
        session_id: Optional[str],
        ip_address: str,
        violation_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security policy violation."""
        violation_details = {"violation_type": violation_type}
        if details:
            violation_details.update(details)
        
        self.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            session_id=session_id,
            ip_address=ip_address,
            details=violation_details,
            success=False
        )
    
    @staticmethod
    def _redact_id(customer_id: str) -> str:
        """Redact customer ID for audit logs."""
        if not customer_id or len(customer_id) < 4:
            return "[redacted]"
        return f"{customer_id[:2]}***{customer_id[-2:]}"
    
    @staticmethod
    def _redact_session(session_id: str) -> str:
        """Redact session ID for audit logs."""
        if not session_id or len(session_id) < 8:
            return "[redacted]"
        return f"{session_id[:4]}...{session_id[-4:]}"


audit_logger = AuditLogger()
