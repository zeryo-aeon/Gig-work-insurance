"""
routers/admin.py — Admin Dashboard API
"""

from fastapi import APIRouter, Request, HTTPException
from models.session import SessionLocal, User, Payment
from services.prediction_service import predictor
from utils.logger import app_logger

router = APIRouter()

@router.get("/users")
async def get_all_users(request: Request):
    """Return all users in the system."""
    app_logger.info("ADMIN: Fetching all registered riders")
    users_list = []
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            # Exclude password hashes for safety
            safe_data = {
                "rider_id": user.rider_id,
                "name": user.name,
                "phone": user.phone,
                "zone": user.zone,
                "platform": user.platform,
                "weekly_plan": user.weekly_plan,
                "active_since": user.active_since,
                "status": "Active" # Mock status
            }
            users_list.append(safe_data)
    finally:
        db.close()
    
    return {"users": users_list}

@router.get("/model-metrics")
async def get_model_metrics(request: Request, rider_id: str):
    """Return X-Y line points of Actual vs Predicted earnings for the XGBoost model."""
    app_logger.info(f"ADMIN: Fetching XGBoost metrics for rider {rider_id}")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.rider_id == rider_id).first()
        if not user:
            app_logger.warning(f"ADMIN: Rider {rider_id} not found for metrics request")
            raise HTTPException(status_code=404, detail="Rider not found")
    finally:
        db.close()
        
    metrics = predictor.get_model_performance(rider_id)
    return metrics

@router.get("/payments")
async def get_payments(request: Request):
    """Fetch all persistent mock payment transactions for admin view from DB."""
    app_logger.info("ADMIN: Fetching all payment transactions from database")
    db = SessionLocal()
    try:
        payments = db.query(Payment).order_by(Payment.timestamp.desc()).all()
        # Convert to list of dicts for frontend
        payment_list = [
            {
                "id": p.id,
                "rider_id": p.rider_id,
                "amount": p.amount,
                "type": p.type,
                "desc": p.desc,
                "timestamp": p.timestamp,
                "date": p.date
            } for p in payments
        ]
        return {"payments": payment_list}
    except Exception as e:
        app_logger.error(f"ADMIN: Error querying payments from DB: {e}")
        return {"payments": []}
    finally:
        db.close()
