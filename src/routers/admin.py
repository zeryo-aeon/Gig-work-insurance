"""
routers/admin.py — Admin Dashboard API
"""

from fastapi import APIRouter, Request, HTTPException
from models.session import USERS_DB
from services.prediction_service import predictor

router = APIRouter()

@router.get("/users")
async def get_all_users(request: Request):
    """Return all users in the system."""
    users_list = []
    for rider_id, data in USERS_DB.items():
        # Exclude password hashes for safety
        safe_data = {
            "rider_id": rider_id,
            "name": data.get("name"),
            "phone": data.get("phone"),
            "zone": data.get("zone"),
            "platform": data.get("platform"),
            "weekly_plan": data.get("weekly_plan"),
            "active_since": data.get("active_since"),
            "status": "Active" # Mock status
        }
        users_list.append(safe_data)
    
    return {"users": users_list}

@router.get("/model-metrics")
async def get_model_metrics(request: Request, rider_id: str):
    """Return X-Y line points of Actual vs Predicted earnings for the XGBoost model."""
    if rider_id not in USERS_DB:
        raise HTTPException(status_code=404, detail="Rider not found")
        
    metrics = predictor.get_model_performance(rider_id)
    return metrics
