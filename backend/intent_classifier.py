"""
Intent classification module.
Determines what the customer is asking for.
"""

from typing import Optional, Tuple
from enum import Enum


class Intent(Enum):
    """Available chatbot intents."""
    SERVICE_ITEMS = "service_items"
    BRANCH_INFO = "branch_info"
    LOAN_PROCESS = "loan_process"
    ACCOUNT_OPENING = "account_opening"
    BANK_ACCOUNT = "bank_account"
    ACCOUNT_BALANCE = "account_balance"
    LOAN_BALANCE = "loan_balance"
    OPENING_BRANCH = "opening_branch"
    GENERAL_HELP = "general_help"
    UNKNOWN = "unknown"


class IntentClassifier:
    """Classifies user input to determine intent."""

    INTENT_KEYWORDS = {
        Intent.SERVICE_ITEMS: [
            "service", "services", "what can you do", "help", "offerings",
            "products", "available services"
        ],
        Intent.BRANCH_INFO: [
            "branch", "branches", "address", "location", "contact", "phone", "hours",
            "where is", "where are", "nearest branch"
        ],
        Intent.LOAN_PROCESS: [
            "loan application", "apply for loan", "borrow", "application process",
            "how to apply", "apply for a loan", "loan process", "get a loan"
        ],
        Intent.ACCOUNT_OPENING: [
            "account", "open", "opening", "new account", "register", "sign up",
            "how to open"
        ],
        Intent.BANK_ACCOUNT: [
            "account number", "account no", "bank account", "my account"
        ],
        Intent.ACCOUNT_BALANCE: [
            "balance", "how much", "available", "account balance",
            "remaining balance"
        ],
        Intent.LOAN_BALANCE: [
            "loan balance", "owe", "outstanding", "debt", "loan amount"
        ],
        Intent.OPENING_BRANCH: [
            "opening branch", "where opened", "which branch", "account from",
            "account opened", "opened account", "branch is my account",
            "where was my account opened", "where did i open"
        ]
    }
    
    @staticmethod
    def classify(user_input: str) -> Tuple[Intent, float]:
        """
        Classify user input to intent.
        Returns: (intent, confidence_score)
        """
        import re
        user_input_lower = user_input.lower()
        scores = {}
        max_keyword_lengths = {}
        
        for intent, keywords in IntentClassifier.INTENT_KEYWORDS.items():
            score = 0
            max_keyword_len = 0
            for keyword in keywords:
                # Use word boundaries to avoid partial matches like "open" matching "opening"
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, user_input_lower):
                    keyword_score = len(keyword.split())
                    score += keyword_score
                    max_keyword_len = max(max_keyword_len, keyword_score)
            scores[intent] = score
            max_keyword_lengths[intent] = max_keyword_len
        
        if max(scores.values()) == 0:
            return Intent.UNKNOWN, 0.0
        
        max_score = max(scores.values())
        best_intent = max(
            [intent for intent, score in scores.items() if score == max_score],
            key=lambda intent: max_keyword_lengths[intent]
        )
        confidence = scores[best_intent] / len(user_input_lower.split())
        
        return best_intent, confidence
    
    @staticmethod
    def get_intent_category(intent: Intent) -> str:
        """Get readable category for intent."""
        category_map = {
            Intent.SERVICE_ITEMS: "Service Information",
            Intent.BRANCH_INFO: "Branch Information",
            Intent.LOAN_PROCESS: "Loan Services",
            Intent.ACCOUNT_OPENING: "Account Services",
            Intent.BANK_ACCOUNT: "Sensitive - Bank Account",
            Intent.ACCOUNT_BALANCE: "Sensitive - Account Balance",
            Intent.LOAN_BALANCE: "Sensitive - Loan Balance",
            Intent.OPENING_BRANCH: "Sensitive - Opening Branch",
            Intent.GENERAL_HELP: "General Help",
            Intent.UNKNOWN: "Unknown"
        }
        return category_map.get(intent, "Unknown")
    
    @staticmethod
    def is_sensitive_query(intent: Intent) -> bool:
        """Check if query requires customer verification."""
        sensitive_intents = {
            Intent.BANK_ACCOUNT,
            Intent.ACCOUNT_BALANCE,
            Intent.LOAN_BALANCE,
            Intent.OPENING_BRANCH
        }
        return intent in sensitive_intents
