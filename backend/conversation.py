"""
Conversation and verification manager.
Manages the state of a customer conversation session.
"""

from typing import Optional, Dict, List
from intent_classifier import Intent, IntentClassifier
from customer_data import CustomerDataManager
from response_handler import ResponseHandler
from security import SecurityValidator, InputValidator
from audit_logger import audit_logger, AuditEventType


class ConversationSession:
    """Manages a single customer conversation session."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.verified_customer_id: Optional[str] = None
        self.verification_attempts = 0
        self.max_verification_attempts = 3
        self.pending_intent: Optional[Intent] = None
        self.conversation_history: List[Dict[str, str]] = []
        
        self.customer_manager = CustomerDataManager()
        self.response_handler = ResponseHandler()
    
    def process_message(self, user_message: str) -> str:
        """
        Process a user message and return a response.
        Handles verification flow and query routing.
        """
        user_message = InputValidator.sanitize_input(user_message)
        self.conversation_history.append({"user": user_message})

        if self.pending_intent and self.is_verification_pending():
            response = self._handle_verification_input(user_message)
            self.conversation_history[-1]["assistant"] = response
            return response
        
        intent, confidence = IntentClassifier.classify(user_message)

        if intent == Intent.UNKNOWN:
            response = (
                "I'm sorry, I didn't understand that. Could you please rephrase your question? "
                "I can help you with service information, branch details, loan/account processes, "
                "or account information."
            )
            self.conversation_history[-1]["assistant"] = response
            return response

        if IntentClassifier.is_sensitive_query(intent):
            if not self.verified_customer_id:
                self.pending_intent = intent
                response = (
                    "For security reasons, I need to verify your identity before providing "
                    "sensitive information.\n\n"
                    "Please provide the following details:\n"
                    "1. Your full name\n"
                    "2. Your date of birth (YYYY/MM/DD)\n"
                    "3. Your ID number"
                )
                self.conversation_history[-1]["assistant"] = response
                return response

        response = self.response_handler.handle_query(intent, self.verified_customer_id)
        
        if IntentClassifier.is_sensitive_query(intent) and self.verified_customer_id:
            audit_logger.log_sensitive_access(
                user_id=self.verified_customer_id,
                session_id=self.session_id,
                ip_address='unknown',
                data_type=intent.name
            )
        
        is_valid, error = SecurityValidator.validate_response(response)
        if not is_valid:
            response = "An error occurred while processing your request. Please try again."
        
        self.conversation_history[-1]["assistant"] = response
        return response
    
    def is_verification_pending(self) -> bool:
        """Check if we're waiting for verification information."""
        return self.pending_intent is not None and self.verified_customer_id is None
    
    def _handle_verification_input(self, user_input: str) -> str:
        """Handle verification data input."""
        import re
        
        self.verification_attempts += 1
        
        if self.verification_attempts > self.max_verification_attempts:
            self.pending_intent = None
            return (
                "Verification failed. For security reasons, I'm unable to proceed. "
                "Please contact our support team or visit a branch."
            )
        
        # Parse verification input
        # Expected format: name, DOB, ID number (can be comma-separated, line-by-line, or labeled)
        # Labeled format: "Name: Tony Stark DOB: 1996/09/10 ID: A234763849"
        
        name = None
        dob = None
        id_number = None
        
        name_match = re.search(r'Name:\s*([^,\n]+?)(?=\s*(?:DOB:|ID:|$))', user_input, re.IGNORECASE)
        dob_match = re.search(r'DOB:\s*([^,\n]+?)(?=\s*(?:Name:|ID:|$))', user_input, re.IGNORECASE)
        id_match = re.search(r'ID:\s*([^,\n]+?)(?=\s*(?:Name:|DOB:|$))', user_input, re.IGNORECASE)
        
        if name_match:
            name = name_match.group(1).strip()
        if dob_match:
            dob = dob_match.group(1).strip()
        if id_match:
            id_number = id_match.group(1).strip()
        
        if not name or not dob or not id_number:
            parts = [p.strip() for p in user_input.replace('\n', ',').split(',')]
            if len(parts) >= 3:
                name = name or parts[0].strip()
                dob = dob or parts[1].strip()
                id_number = id_number or parts[2].strip()
        
        if not name or not dob or not id_number:
            remaining = sum([not name, not dob, not id_number])
            return (
                f"Please provide all required information. "
                f"You still need to provide {remaining} more field(s).\n"
                f"Format: Name, Date of Birth (YYYY/MM/DD), ID Number\n"
                f"Or use labeled format: Name: [name] DOB: [date] ID: [id]"
            )
 
        success, result = self.customer_manager.verify_customer(name, dob, id_number)
        
        if not success:
            attempts_remaining = self.max_verification_attempts - self.verification_attempts
            audit_logger.log_event(
                event_type=AuditEventType.VERIFICATION_FAILURE,
                session_id=self.session_id,
                details={
                    "attempts": self.verification_attempts,
                    "attempts_remaining": attempts_remaining,
                    "reason": result
                }
            )
            
            if attempts_remaining > 0:
                return (
                    f"Verification failed: {result}\n"
                    f"Attempts remaining: {attempts_remaining}\n"
                    f"Please try again with correct information."
                )
            else:
                self.pending_intent = None
                return (
                    "Verification failed. For security reasons, I'm unable to proceed. "
                    "Please contact our support team or visit a branch."
                )
        
        self.verified_customer_id = result
        self.verification_attempts = 0
        
        audit_logger.log_event(
            event_type=AuditEventType.VERIFICATION_SUCCESS,
            session_id=self.session_id,
            user_id=result,
            details={"attempts": self.verification_attempts}
        )
        
        intent = self.pending_intent
        self.pending_intent = None

        response = self.response_handler.handle_query(intent, self.verified_customer_id)
        response = f"✓ Identity verified successfully!\n\n{response}"
        
        return response
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the full conversation history."""
        return self.conversation_history
    
    def reset_verification(self) -> None:
        """Reset verification status (for logout/new session)."""
        self.verified_customer_id = None
        self.verification_attempts = 0
        self.pending_intent = None
