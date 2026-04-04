"""
routers/insurance.py — Insurance plans & pricing API
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from models.session import get_current_user
from utils.logger import app_logger

router = APIRouter()


def require_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_current_user(token)


PLANS = [
    {
        "id": "basic",
        "name": "Basic Protection",
        "base_price": 30,
        "description": "Essential coverage for income loss. 60% of daily average covered on trigger. Micro-savings matches.",
        "coverage_level": 1.0,
        "guarantee": "60% income loss protected",
    },
    {
        "id": "medium",
        "name": "Professional Plus",
        "base_price": 50,
        "description": "Standard professional coverage. 80% coverage + hazard multiplier during extreme conditions.",
        "coverage_level": 1.25,
        "guarantee": "80% income + hazard bonus",
    },
    {
        "id": "ultra",
        "name": "Ultra Shield",
        "base_price": 80,
        "description": "Premium 100% income protection. Zero-touch refunds on safe days and peak payout guarantees.",
        "coverage_level": 1.5,
        "guarantee": "100% full income buffer",
    }
]


@router.get("/plans")
async def get_plans(request: Request):
    user = require_auth(request)
    app_logger.info(f"INSURANCE: Fetching available plans for rider {user.rider_id}")
    return {"plans": PLANS}


from services.prediction_service import predictor

@router.get("/ai-premium")
async def get_ai_premium(request: Request, plan_id: str = "basic"):
    user = require_auth(request)
    app_logger.info(f"INSURANCE: Calculating AI premium for rider {user.rider_id} (Tier: {plan_id})")
    plan = next((p for p in PLANS if p["id"] == plan_id), PLANS[0])
    
    # Dynamic calculation using our expanded Points Engine
    pricing_res = predictor.calculate_premium_modifier(user.rider_id, zone=user.zone)
    
    # Extract components
    modifier = pricing_res["modifier"]
    total_points = pricing_res["points_total"]
    points_discount = pricing_res["discount_applied"]
    
    coverage_multiplier = plan["coverage_level"]
    
    # Formula: (Base + Dynamic Offset from Points) * Risk Modifier
    # Points reduce the base (positive points = lower base)
    dynamic_base = plan["base_price"] - points_discount
    premium = (dynamic_base * modifier * coverage_multiplier)
    
    premium_rounded = round(premium / 5) * 5  # round to nearest 5
    
    return {
        "plan_id": plan_id,
        "points": {
            "total": total_points,
            "breakdown": pricing_res["points_breakdown"]
        },
        "formula": {
            "tier_base": plan["base_price"],
            "points_adjustment": -points_discount,
            "dynamic_base": round(dynamic_base, 2),
            "risk_modifier": round(modifier, 2),
            "coverage_multiplier": coverage_multiplier,
        },
        "final_premium": float(max(5.0, premium_rounded)),
        "tier_rating": "High Risk" if modifier > 1.3 else "Optimal" if total_points > 20 else "Standard",
        "insights": pricing_res["insights"],
        "weather_input": "Live Data (Open-Meteo)",
        "location_input": f"Dynamic (Zone: {user.zone})",
        "earnings_input": "XGBoost Prediction Model",
    }


class ActivatePlanRequest(BaseModel):
    plan_id: str


@router.post("/activate")
async def activate_plan(request: Request, body: ActivatePlanRequest):
    user = require_auth(request)
    app_logger.info(f"INSURANCE: Rider {user.rider_id} activating plan: {body.plan_id}")
    plan = next((p for p in PLANS if p["id"] == body.plan_id), None)
    if not plan:
        app_logger.error(f"INSURANCE: Invalid plan ID {body.plan_id} requested by {user.rider_id}")
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    return {
        "success": True,
        "message": f"Plan '{plan['name']}' activated for {user.name}",
        "rider_id": user.rider_id,
        "plan": plan,
        "effective": "Week of 16–22 Jun 2025",
    }
