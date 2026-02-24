"""
Configuration and constants for the bank customer service chatbot.
"""

CUSTOMERS = {
    "A234763849": {
        "name": "Tony Stark",
        "dob": "1996/09/10",
        "id_number": "A234763849",
        "bank_account": "6102394256679291",
        "account_balance": "TWD 2,500,394",
        "loan_balance": "TWD 19,243,225",
        "opening_branch": "Taipei First Main Branch"
    }
}

SERVICE_ITEMS = [
    "24/7 Customer Support",
    "Account Management",
    "Loan Services",
    "Investment Advisory",
    "Credit Card Services",
    "Mobile Banking"
]

BRANCHES = {
    "Taipei First Main Branch": {
        "address": "No. 1, Dunnan Rd, Taipei",
        "phone": "02-2109-5500",
        "hours": "Mon-Fri 9:00-17:00"
    },
    "Taipei Second Branch": {
        "address": "No. 88, Songshan Rd, Taipei",
        "phone": "02-2719-7000",
        "hours": "Mon-Fri 9:00-17:00"
    }
}

LOAN_PROCESS = [
    "1. Submit application with required documents",
    "2. Credit assessment and verification",
    "3. Final approval decision",
    "4. Loan disbursement"
]

ACCOUNT_OPENING_PROCESS = [
    "1. Visit nearest branch with valid ID",
    "2. Fill out account opening form",
    "3. Provide initial deposit (min TWD 1,000)",
    "4. Activate online banking (optional)",
    "5. Receive debit card in 7-10 business days"
]

SENSITIVE_QUERIES = [
    "bank_account",
    "account_balance",
    "loan_balance",
    "opening_branch"
]

VERIFICATION_FIELDS = ["name", "dob", "id_number"]
