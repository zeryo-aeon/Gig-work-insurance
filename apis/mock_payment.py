import uuid
import time
from typing import Dict, Any

class MockPaymentSystem:
    def __init__(self):
        """Initialize the mock payment system."""
        pass

    def process_premium(self, rider_id: str, amount: float) -> Dict[str, Any]:
        """Simulate charging a weekly premium to a gig worker."""
        # Simulate network delay
        time.sleep(0.3)
        transaction_id = f"txn_prem_{uuid.uuid4().hex[:8]}"
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "rider_id": rider_id,
            "amount": amount,
            "type": "premium_charge",
            "message": f"Successfully charged ₹{amount} to rider {rider_id}"
        }

    def process_payout(self, rider_id: str, amount: float, reason: str) -> Dict[str, Any]:
        """Simulate paying out an insurance claim to a gig worker automatically."""
        # Simulate network delay
        time.sleep(0.3)
        transaction_id = f"txn_pay_{uuid.uuid4().hex[:8]}"
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "rider_id": rider_id,
            "amount": amount,
            "type": "insurance_payout",
            "reason": reason,
            "message": f"Successfully paid ₹{amount} to rider {rider_id} for {reason}"
        }
    
    def get_wallet_balance(self, rider_id: str) -> Dict[str, Any]:
        """Simulate fetching a rider's wallet balance."""
        return {
            "rider_id": rider_id,
            "balance_inr": 1250.00,  # Mock static balance
            "status": "active"
        }

if __name__ == "__main__":
    payment_sys = MockPaymentSystem()
    print(payment_sys.process_premium("GW-8821", 60.0))
    print(payment_sys.process_payout("GW-8821", 340.0, "Heavy Rain Trigger"))
