"""
Customer data management module.
Handles customer information securely and provides verification.
"""

from typing import Optional, Dict, Any
from config import CUSTOMERS, VERIFICATION_FIELDS
from security import InputValidator


class CustomerDataManager:
    """Manages customer data and verification."""
    
    def __init__(self):
        self.customers = CUSTOMERS
    
    def verify_customer(self, name: str, dob: str, id_number: str) -> tuple[bool, Optional[str]]:
        """
        Verify customer identity against stored data.
        Returns: (verification_success, customer_id_if_successful)
        """
        # Validate input formats
        if not InputValidator.validate_name(name):
            return False, "Invalid name format"
        
        if not InputValidator.validate_dob(dob):
            return False, "Invalid date of birth format (use YYYY/MM/DD)"
        
        if not InputValidator.validate_id_number(id_number):
            return False, "Invalid ID number format"
  
        if id_number not in self.customers:
            return False, "Customer ID not found"
        
        customer = self.customers[id_number]
 
        if customer["name"].lower() != name.lower():
            return False, "Name does not match"
        
        if customer["dob"] != dob:
            return False, "Date of birth does not match"
        
        if customer["id_number"] != id_number:
            return False, "ID number does not match"
        
        return True, id_number
    
    def get_customer_info(self, customer_id: str, field: str) -> Optional[str]:
        """
        Get specific customer information.
        Only callable after verification.
        """
        if customer_id not in self.customers:
            return None
        
        customer = self.customers[customer_id]
        return customer.get(field)
    
    def get_all_customer_fields(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get all customer information fields."""
        if customer_id not in self.customers:
            return None
        return self.customers[customer_id]
    
    def customer_exists(self, id_number: str) -> bool:
        """Check if customer exists in database."""
        return id_number in self.customers
