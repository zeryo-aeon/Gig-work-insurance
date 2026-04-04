import uuid
import time
from typing import Dict, Any, List

try:
    from utils.logger import app_logger
    from models.database import SessionLocal
    from models.session import Payment, User
except ImportError:
    import logging
    app_logger = logging.getLogger("MockPaymentWrapper")
    # Fallback/Mock for local testing if src not in path
    SessionLocal = None

class MockPaymentWrapper:
    def __init__(self):
        """Initialize the mock payment system with database persistence."""
        pass

    def process_premium(self, rider_id: str, amount: float) -> Dict[str, Any]:
        """Simulate charging a weekly premium to a gig worker."""
        app_logger.info(f"PAYMENT: Charging premium ₹{amount} to rider {rider_id}")
        time.sleep(0.3)
        transaction_id = f"txn_prem_{uuid.uuid4().hex[:8]}"
        
        if SessionLocal:
            db = SessionLocal()
            try:
                txn = Payment(
                    id=transaction_id,
                    rider_id=rider_id,
                    amount=-amount,
                    type="premium_charge",
                    desc="Weekly Insurance Premium",
                    timestamp=time.time(),
                    date=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                db.add(txn)
                db.commit()
                app_logger.info(f"PAYMENT: Persistent record created: {transaction_id}")
            finally:
                db.close()
        
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
        app_logger.info(f"PAYMENT: Initiating payout ₹{amount} to rider {rider_id} for {reason}")
        time.sleep(0.3)
        transaction_id = f"txn_pay_{uuid.uuid4().hex[:8]}"
        
        if SessionLocal:
            db = SessionLocal()
            try:
                txn = Payment(
                    id=transaction_id,
                    rider_id=rider_id,
                    amount=amount,
                    type="insurance_payout",
                    desc=reason,
                    timestamp=time.time(),
                    date=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                db.add(txn)
                db.commit()
                app_logger.info(f"PAYMENT: Persistent record created: {transaction_id}")
            finally:
                db.close()
        
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
        """Simulate fetching a rider's wallet balance from database history."""
        app_logger.debug(f"PAYMENT: Calculating balance from DB for rider {rider_id}")
        
        balance = 1000.00 # Base
        
        if SessionLocal:
            db = SessionLocal()
            try:
                payments = db.query(Payment).filter(Payment.rider_id == rider_id).all()
                balance += sum(p.amount for p in payments)
            finally:
                db.close()
        
        return {
            "rider_id": rider_id,
            "balance_inr": round(balance, 2),
            "status": "active"
        }

if __name__ == "__main__":
    # Test block
    payment_sys = MockPaymentWrapper()
    print(payment_sys.get_wallet_balance("GW-8821"))

