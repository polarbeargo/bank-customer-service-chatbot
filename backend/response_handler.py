"""
Response handler module.
Generates appropriate responses based on intent and verification status.
"""

from typing import Optional
from intent_classifier import Intent, IntentClassifier
from customer_data import CustomerDataManager
from config import SERVICE_ITEMS, BRANCHES, LOAN_PROCESS, ACCOUNT_OPENING_PROCESS
from security import SecurityValidator


class ResponseHandler:
    """Generates responses to customer queries."""
    
    def __init__(self):
        self.customer_manager = CustomerDataManager()
    
    def handle_query(
        self,
        intent: Intent,
        verified_customer_id: Optional[str] = None
    ) -> str:
        """
        Generate response based on intent and verification status.
        Returns: Response string
        """

        if IntentClassifier.is_sensitive_query(intent):
            if not verified_customer_id:
                return (
                    "For security reasons, I need to verify your identity first. "
                    "Please provide your name, date of birth (YYYY/MM/DD), and ID number."
                )
            return self._handle_sensitive_query(intent, verified_customer_id)
        
        return self._handle_public_query(intent)
    
    def _handle_public_query(self, intent: Intent) -> str:
        """Handle queries that don't require verification."""
        
        if intent == Intent.SERVICE_ITEMS:
            return self._format_service_items()
        
        elif intent == Intent.BRANCH_INFO:
            return self._format_branch_info()
        
        elif intent == Intent.LOAN_PROCESS:
            return self._format_loan_process()
        
        elif intent == Intent.ACCOUNT_OPENING:
            return self._format_account_opening()
        
        elif intent == Intent.GENERAL_HELP:
            return self._format_general_help()
        
        else:
            return (
                "I'm sorry, I didn't understand your question. "
                "I can help you with:\n"
                "- Service items available\n"
                "- Branch locations and contact information\n"
                "- Loan application process\n"
                "- Account opening process\n"
                "- Account-related information (with verification)"
            )
    
    def _handle_sensitive_query(self, intent: Intent, customer_id: str) -> str:
        """Handle sensitive queries that require customer verification."""
        
        if intent == Intent.BANK_ACCOUNT:
            account = self.customer_manager.get_customer_info(customer_id, "bank_account")
            return f"Your bank account number is: {account}"
        
        elif intent == Intent.ACCOUNT_BALANCE:
            balance = self.customer_manager.get_customer_info(customer_id, "account_balance")
            return f"Your current account balance is: {balance}"
        
        elif intent == Intent.LOAN_BALANCE:
            loan_balance = self.customer_manager.get_customer_info(customer_id, "loan_balance")
            return f"Your current loan balance is: {loan_balance}"
        
        elif intent == Intent.OPENING_BRANCH:
            branch = self.customer_manager.get_customer_info(customer_id, "opening_branch")
            return f"Your account was opened at: {branch}"
        
        else:
            return "Unable to process your request."
    
    def _format_service_items(self) -> str:
        """Format service items response."""
        items_str = "\n".join([f"- {item}" for item in SERVICE_ITEMS])
        return f"Our available services are:\n{items_str}"
    
    def _format_branch_info(self) -> str:
        """Format branch information response."""
        branch_info = []
        for branch_name, info in BRANCHES.items():
            branch_info.append(
                f"📍 {branch_name}\n"
                f"   Address: {info['address']}\n"
                f"   Phone: {info['phone']}\n"
                f"   Hours: {info['hours']}"
            )
        return "Our branches:\n\n" + "\n\n".join(branch_info)
    
    def _format_loan_process(self) -> str:
        """Format loan application process response."""
        process_str = "\n".join(LOAN_PROCESS)
        return f"Loan Application Process:\n{process_str}\n\nFor more details, please visit our website or contact your nearest branch."
    
    def _format_account_opening(self) -> str:
        """Format account opening process response."""
        process_str = "\n".join(ACCOUNT_OPENING_PROCESS)
        return f"Account Opening Process:\n{process_str}\n\nFor assistance, please visit your nearest branch."
    
    def _format_general_help(self) -> str:
        """Format general help response."""
        return (
            "Hello! I'm your bank customer service assistant. I can help you with:\n"
            "1. Service items and offerings\n"
            "2. Branch locations and contact information\n"
            "3. Loan application process\n"
            "4. Account opening process\n"
            "5. Account information (with verification)\n\n"
            "How can I assist you today?"
        )
