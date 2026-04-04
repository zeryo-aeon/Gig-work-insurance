import json
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, engine
from models.session import User, Payment, RiderHistory, Base
from utils.logger import app_logger

def migrate():
    """Migrate data from JSON files to SQLite database."""
    app_logger.info("MIGRATION: Starting data migration from JSON to SQLite")
    db = SessionLocal()
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    history_file = os.path.join(BASE_DIR, "data", "rider_history.json")
    payments_file = os.path.join(BASE_DIR, "data", "payments.json")

    # 1. Migrate Rider History
    if os.path.exists(history_file):
        app_logger.info(f"MIGRATION: Loading history from {history_file}")
        with open(history_file, "r") as f:
            history_data = json.load(f)
        
        count = 0
        for rider_id, data in history_data.items():
            # Check if user exists
            user = db.query(User).filter(User.rider_id == rider_id).first()
            if not user:
                app_logger.warning(f"MIGRATION: User {rider_id} not found in DB. Skipping history.")
                continue
            
            for item in data.get("history", []):
                # Check if already exists to avoid duplicates
                exists = db.query(RiderHistory).filter(
                    RiderHistory.rider_id == rider_id,
                    RiderHistory.date == item["date"]
                ).first()
                
                if not exists:
                    rh = RiderHistory(
                        rider_id=rider_id,
                        date=item["date"],
                        earnings=item["earnings"],
                        hours_worked=item["hours_worked"],
                        weather_risk_score=item["weather_risk_score"],
                        payouts=item["payouts"],
                        trips=item["trips"],
                        origin_address=item["origin_address"],
                        destination_address=item["destination_address"],
                        route_distance_km=item["route_distance_km"],
                        route_eta_mins=item["route_eta_mins"],
                        traffic_delay_mins=item["traffic_delay_mins"]
                    )
                    db.add(rh)
                    count += 1
        db.commit()
        app_logger.info(f"MIGRATION: Successfully migrated {count} history records.")

    # 2. Migrate Payments
    if os.path.exists(payments_file):
        app_logger.info(f"MIGRATION: Loading payments from {payments_file}")
        with open(payments_file, "r") as f:
            payments_data = json.load(f)
        
        count = 0
        for p in payments_data:
            # Check if already exists
            exists = db.query(Payment).filter(Payment.id == p["id"]).first()
            if not exists:
                pay = Payment(
                    id=p["id"],
                    rider_id=p["rider_id"],
                    amount=p["amount"],
                    type=p["type"],
                    desc=p["desc"],
                    timestamp=p["timestamp"],
                    date=p["date"]
                )
                db.add(pay)
                count += 1
        db.commit()
        app_logger.info(f"MIGRATION: Successfully migrated {count} payment records.")

    db.close()
    app_logger.info("MIGRATION: Completed successfully.")

if __name__ == "__main__":
    migrate()
