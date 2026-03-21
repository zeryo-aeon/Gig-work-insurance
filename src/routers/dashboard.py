"""
routers/dashboard.py — Dashboard data API
"""

from fastapi import APIRouter, Request, HTTPException
from models.session import get_current_user
import random
import os
import sys

# Ensure apis is searchable
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apis.openmentoapi import OpenMeteoWrapper
from apis.mock_payment import MockPaymentSystem

router = APIRouter()
weather_client = OpenMeteoWrapper()
payment_client = MockPaymentSystem()


def require_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_current_user(token)


@router.get("/summary")
async def get_summary(request: Request):
    user = require_auth(request)
    
    # Fetch real live weather data (defaulting to Bangalore for demo)
    user_zone = user.dict().get("zone", "Bangalore")
    weather = weather_client.get_city_data(user_zone)
    
    # Get mock balance
    balance_data = payment_client.get_wallet_balance(user.rider_id)
    
    # Determine statuses based on thresholds
    temp_val = weather["current"].get("temperature_2m", 0)
    rain_val = weather["current"].get("precipitation", 0)
    aqi_val = weather["air_quality"].get("pm2_5", 0)
    
    return {
        "rider": user.dict(),
        "wallet_balance": balance_data["balance"],
        "week": {
            "label": "Live Performance",
            "earnings": 4820,
            "payout": 680,
            "premium": 82,
            "risk_score": 68,
            "triggers_fired": 2,
        },
        "environment": {
            "temperature": {"value": round(temp_val,1), "unit": "°C", "status": "warn" if temp_val > 35 else "clear", "threshold": 35},
            "rainfall": {"value": round(rain_val,1), "unit": "mm", "status": "triggered" if rain_val > 5 else "clear", "threshold": 5},
            "aqi": {"value": round(aqi_val,1), "unit": "μg/m³", "status": "warn" if aqi_val > 50 else "clear", "threshold": 50},
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
