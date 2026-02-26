"""
Unit tests for the bank customer service chatbot.
Run with: python3 test_chatbot.py 
"""

import sys
sys.path.insert(0, '.')

from security import SecurityValidator, InputValidator
from customer_data import CustomerDataManager
from intent_classifier import IntentClassifier, Intent
from conversation import ConversationSession


class TestSecurityValidator:
    """Test security validation functions."""
    
    def test_contains_forbidden_keywords(self):
        """Test detection of forbidden keywords."""
        assert SecurityValidator.contains_sensitive_data("Your password is 123")
        assert SecurityValidator.contains_sensitive_data("Enter your PIN")
        assert SecurityValidator.contains_sensitive_data("Your api_key is xxx")
        assert not SecurityValidator.contains_sensitive_data("Your account balance is 5000")
    
    def test_validate_response(self):
        """Test response validation."""
        valid, error = SecurityValidator.validate_response("Your balance is 5000")
        assert valid
        
        valid, error = SecurityValidator.validate_response("Your password is secret123")
        assert not valid


class TestInputValidator:
    """Test input validation functions."""
    
    def test_validate_id_number(self):
        """Test Taiwan ID number validation."""
        assert InputValidator.validate_id_number("A234763849")
        assert not InputValidator.validate_id_number("234763849")  # Missing letter
        assert not InputValidator.validate_id_number("AA23476384")  # Two letters
    
    def test_validate_dob(self):
        """Test date of birth validation."""
        assert InputValidator.validate_dob("1996/09/10")
        assert not InputValidator.validate_dob("1996-09-10")  # Wrong separator
        assert not InputValidator.validate_dob("09/10/1996")  # Wrong order
    
    def test_validate_name(self):
        """Test name validation."""
        assert InputValidator.validate_name("Tony Stark")
        assert InputValidator.validate_name("John")
        assert not InputValidator.validate_name("A")  # Too short
        assert not InputValidator.validate_name("DROP TABLE; --")  # SQL injection attempt


class TestCustomerDataManager:
    """Test customer data management."""
    
    def test_verify_customer_success(self):
        """Test successful customer verification."""
        manager = CustomerDataManager()
        success, customer_id = manager.verify_customer("Tony Stark", "1996/09/10", "A234763849")
        assert success
        assert customer_id == "A234763849"
    
    def test_verify_customer_wrong_name(self):
        """Test verification with wrong name."""
        manager = CustomerDataManager()
        success, message = manager.verify_customer("John Doe", "1996/09/10", "A234763849")
        assert not success
        assert "name" in message.lower()
    
    def test_verify_customer_wrong_dob(self):
        """Test verification with wrong date of birth."""
        manager = CustomerDataManager()
        success, message = manager.verify_customer("Tony Stark", "1990/01/01", "A234763849")
        assert not success
        assert "birth" in message.lower()
    
    def test_get_customer_info(self):
        """Test retrieving customer information."""
        manager = CustomerDataManager()
        balance = manager.get_customer_info("A234763849", "account_balance")
        assert "TWD 2,500,394" in balance


class TestIntentClassifier:
    """Test intent classification."""
    
    def test_classify_service_items(self):
        """Test classification of service queries."""
        intent, confidence = IntentClassifier.classify("What services do you offer?")
        assert intent == Intent.SERVICE_ITEMS
    
    def test_classify_branch_info(self):
        """Test classification of branch queries."""
        intent, confidence = IntentClassifier.classify("Where are your branches?")
        assert intent == Intent.BRANCH_INFO
    
    def test_classify_account_balance(self):
        """Test classification of account balance queries."""
        intent, confidence = IntentClassifier.classify("What is my account balance?")
        assert intent == Intent.ACCOUNT_BALANCE
    
    def test_is_sensitive_query(self):
        """Test identification of sensitive queries."""
        assert IntentClassifier.is_sensitive_query(Intent.ACCOUNT_BALANCE)
        assert IntentClassifier.is_sensitive_query(Intent.BANK_ACCOUNT)
        assert not IntentClassifier.is_sensitive_query(Intent.SERVICE_ITEMS)


class TestConversationSession:
    """Test conversation session management."""
    
    def test_public_query(self):
        """Test handling of public queries."""
        session = ConversationSession()
        response = session.process_message("What services do you offer?")
        assert "24/7 Customer Support" in response
    
    def test_sensitive_query_without_verification(self):
        """Test that sensitive queries require verification."""
        session = ConversationSession()
        response = session.process_message("What is my account balance?")
        assert "verify" in response.lower() or "verification" in response.lower()
    
    def test_verification_flow(self):
        """Test complete verification flow."""
        session = ConversationSession()
        
        response1 = session.process_message("What is my account balance?")
        assert "identity" in response1.lower()

        response2 = session.process_message("Tony Stark, 1996/09/10, A234763849")
        assert "verified" in response2.lower()
        assert "2,500,394" in response2
    
    def test_failed_verification(self):
        """Test failed verification attempts."""
        session = ConversationSession()

        session.process_message("What is my account balance?")
        
        response = session.process_message("John Doe, 1990/01/01, B123456789")
        assert "failed" in response.lower() or "not found" in response.lower()
    
    def test_conversation_history(self):
        """Test conversation history tracking."""
        session = ConversationSession()
        session.process_message("What services do you offer?")
        
        history = session.get_conversation_history()
        assert len(history) > 0
        assert "assistant" in history[0]


def run_tests():
    """Run all tests and display results."""
    test_classes = [
        TestSecurityValidator,
        TestInputValidator,
        TestCustomerDataManager,
        TestIntentClassifier,
        TestConversationSession
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    print("\n" + "="*60)
    print("RUNNING CHATBOT TESTS")
    print("="*60 + "\n")
    
    for test_class in test_classes:
        print(f"\nTesting {test_class.__name__}...")
        test_instance = test_class()
        
        for method_name in dir(test_instance):
            if method_name.startswith('test_'):
                total_tests += 1
                try:
                    method = getattr(test_instance, method_name)
                    method()
                    print(f"  ✓ {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {str(e)}")
                    failed_tests.append((test_class.__name__, method_name, str(e)))
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {len(failed_tests)}")
    
    if failed_tests:
        print("\nFailed Tests:")
        for class_name, method_name, error in failed_tests:
            print(f"  - {class_name}.{method_name}: {error}")
    else:
        print("\n✓ All tests passed!")
    
    print()


if __name__ == "__main__":
    run_tests()
