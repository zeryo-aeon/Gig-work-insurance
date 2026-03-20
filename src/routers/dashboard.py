"""
routers/dashboard.py — Dashboard data API
"""

from fastapi import APIRouter, Request, HTTPException
from models.session import get_current_user
import random

router = APIRouter()


def require_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_current_user(token)


@router.get("/summary")
async def get_summary(request: Request):
    user = require_auth(request)
    return {
        "rider": user.dict(),
        "week": {
            "label": "16–22 Jun 2025",
            "earnings": 4820,
            "payout": 680,
            "premium": 82,
            "risk_score": 68,
            "triggers_fired": 2,
        },
        "environment": {
            "temperature": {"value": 38, "unit": "°C", "status": "watch", "threshold": 42},
            "rainfall": {"value": 48, "unit": "mm/hr", "status": "triggered", "threshold": 30},
            "aqi": {"value": 142, "unit": "AQI", "status": "clear", "threshold": 300},
            "mobility": {"value": "Normal", "unit": "", "status": "clear", "threshold": "Any restriction"},
            "platform": {"value": "Online", "unit": "", "status": "clear", "threshold": "Downtime"},
        }
    }


@router.get("/earnings-chart")
async def get_earnings_chart(request: Request):
    user = require_auth(request)
    return {
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "earnings": [820, 760, 680, 0, 900, 1100, 560],
        "payouts": [0, 0, 340, 380, 0, 0, 0],
        "expected": [800, 800, 800, 800, 800, 800, 800],
    }


@router.get("/risk-factors")
async def get_risk_factors(request: Request):
    user = require_auth(request)
    return {
        "overall_score": 68,
        "level": "High",
        "factors": [
            {"name": "Weather", "score": 80, "color": "warn"},
            {"name": "Mobility", "score": 25, "color": "green"},
            {"name": "Platform", "score": 15, "color": "green"},
            {"name": "Income Var.", "score": 60, "color": "gold"},
        ]
    }


@router.get("/disruptions")
async def get_disruptions(request: Request):
    user = require_auth(request)
    return {
        "disruptions": [
            {
                "name": "Heavy Rain",
                "type": "Environmental",
                "icon": "🌧️",
                "measured": "48 mm/hr",
                "threshold": "> 30 mm/hr",
                "loss": "₹340",
                "status": "triggered"
            },
            {
                "name": "Extreme Heat",
                "type": "Environmental",
                "icon": "🌡️",
                "measured": "38°C",
                "threshold": "> 42°C",
                "loss": "—",
                "status": "watch"
            },
            {
                "name": "Air Pollution",
                "type": "Environmental",
                "icon": "💨",
                "measured": "142 AQI",
                "threshold": "> 300 AQI",
                "loss": "—",
                "status": "clear"
            },
            {
                "name": "Zone Curfew",
                "type": "Social",
                "icon": "🚫",
                "measured": "No alerts",
                "threshold": "Any alert",
                "loss": "—",
                "status": "clear"
            },
            {
                "name": "Demand Crash",
                "type": "Platform",
                "icon": "📉",
                "measured": "Orders/hr: 8",
                "threshold": "< 5 orders/hr",
                "loss": "—",
                "status": "clear"
            },
        ]
    }
