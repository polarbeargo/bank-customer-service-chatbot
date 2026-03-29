"""
Intent classification module.
Determines what the customer is asking for.
"""

import re
from enum import Enum
from typing import Dict, List, Pattern, Tuple


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

    COMPILED_INTENT_PATTERNS: Dict[Intent, List[Tuple[Pattern[str], int]]] = {
        intent: [
            (re.compile(r'\b' + re.escape(keyword) + r'\b'), len(keyword.split()))
            for keyword in keywords
        ]
        for intent, keywords in INTENT_KEYWORDS.items()
    }
    
    @staticmethod
    def classify(user_input: str) -> Tuple[Intent, float]:
        """
        Classify user input to intent.
        Returns: (intent, confidence_score)
        """
        user_input_lower = user_input.lower()
        token_count = max(len(user_input_lower.split()), 1)
        best_intent = Intent.UNKNOWN
        best_score = 0
        best_max_keyword_len = 0

        for intent, patterns in IntentClassifier.COMPILED_INTENT_PATTERNS.items():
            score = 0
            max_keyword_len = 0
            for pattern, keyword_score in patterns:
                if pattern.search(user_input_lower):
                    score += keyword_score
                    max_keyword_len = max(max_keyword_len, keyword_score)

            if score > best_score or (score == best_score and max_keyword_len > best_max_keyword_len):
                best_intent = intent
                best_score = score
                best_max_keyword_len = max_keyword_len

        if best_score == 0:
            return Intent.UNKNOWN, 0.0

        confidence = best_score / token_count
        
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
