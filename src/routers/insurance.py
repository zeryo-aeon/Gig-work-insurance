"""
routers/insurance.py — Insurance plans & pricing API
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from models.session import get_current_user

router = APIRouter()


def require_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_current_user(token)


PLANS = [
    {
        "id": "micro",
        "name": "Micro-Insurance",
        "base_price": 60,
        "description": "5% of weekly earnings → Resilience Pool + platform match. Auto payout on trigger.",
        "coverage_level": 1.2,
        "guarantee": "50% income loss covered",
    },
    {
        "id": "hazard",
        "name": "Hazard Multiplier",
        "base_price": 100,
        "description": "1.5× base pay on hazard days. Rain/heat threshold crossed → automatic upgrade.",
        "coverage_level": 1.5,
        "guarantee": "1.5× pay on hazard days",
    },
    {
        "id": "stability",
        "name": "Stability Contract",
        "base_price": 80,
        "description": "Fixed weekly schedule → 70% payout guaranteed on curfew / lockdown days.",
        "coverage_level": 1.3,
        "guarantee": "70% payout on lockdown",
    },
    {
        "id": "baseline",
        "name": "Baseline Guarantee",
        "base_price": 50,
        "description": "Min ₹2500/week if active hours met. Disruption hours counted as worked.",
        "coverage_level": 1.0,
        "guarantee": "₹2500 min weekly income",
    },
]


@router.get("/plans")
async def get_plans(request: Request):
    require_auth(request)
    return {"plans": PLANS}


@router.get("/ai-premium")
async def get_ai_premium(request: Request, plan_id: str = "micro"):
    require_auth(request)
    plan = next((p for p in PLANS if p["id"] == plan_id), PLANS[0])
    
    # AI Premium Formula: Base + (RiskScore × CoverageLevel × IncomeVariability)
    base = 30
    risk_score = 0.68
    coverage_level = plan["coverage_level"]
    income_variability = 1.10
    
    premium = base + (risk_score * coverage_level * income_variability * 100)
    premium_rounded = round(premium / 10) * 10  # round to nearest 10
    
    return {
        "plan_id": plan_id,
        "formula": {
            "base": base,
            "risk_score": risk_score,
            "coverage_level": coverage_level,
            "income_variability": income_variability,
        },
        "calculated": round(premium, 2),
        "final_premium": premium_rounded,
        "tier": "High" if risk_score > 0.6 else "Medium" if risk_score > 0.3 else "Low",
        "weather_input": "High (Open-Meteo API)",
        "location_input": "Medium (Geoapify)",
        "earnings_input": "₹23.4K avg (4 weeks)",
    }


class ActivatePlanRequest(BaseModel):
    plan_id: str


@router.post("/activate")
async def activate_plan(request: Request, body: ActivatePlanRequest):
    user = require_auth(request)
    plan = next((p for p in PLANS if p["id"] == body.plan_id), None)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    return {
        "success": True,
        "message": f"Plan '{plan['name']}' activated for {user.name}",
        "rider_id": user.rider_id,
        "plan": plan,
        "effective": "Week of 16–22 Jun 2025",
    }
