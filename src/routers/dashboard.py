"""
routers/dashboard.py — Dashboard data API
"""

from fastapi import APIRouter, Request, HTTPException
from models.session import get_current_user
import random
import os
import sys
from datetime import datetime

# Ensure apis is searchable
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apis.openmentoapi import OpenMeteoWrapper
from apis.mock_payment import MockPaymentSystem
from services.prediction_service import predictor
import json

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rider_history.json")

def load_history_for_rider(rider_id: str):
    if not os.path.exists(HISTORY_FILE):
        return None
    with open(HISTORY_FILE, "r") as f:
        data = json.load(f)
        return data.get(rider_id)

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
    try:
        user = require_auth(request)
        
        # Fetch real live weather data
        user_zone = user.dict().get("zone", "Bangalore")
        weather = weather_client.get_city_data(user_zone)
        
        # Get mock balance
        balance_data = payment_client.get_wallet_balance(user.rider_id)
        
        # Historical data to calculate current week stats
        rider_data = load_history_for_rider(user.rider_id)
        total_earnings = 0
        total_payouts = 0
        total_distance = 0
        total_traffic_delay = 0
        recent_route = {}
        
        if rider_data and "history" in rider_data and len(rider_data["history"]) > 0:
            total_earnings = sum(h["earnings"] for h in rider_data["history"])
            total_payouts = sum(h["payouts"] for h in rider_data["history"])
            total_distance = sum(h.get("route_distance_km", 0) for h in rider_data["history"])
            total_traffic_delay = sum(h.get("traffic_delay_mins", 0) for h in rider_data["history"])
            # Get most recent route
            latest = sorted(rider_data["history"], key=lambda x: x["date"], reverse=True)[0]
            recent_route = {
                "origin": latest.get("origin_address", "Unknown"),
                "destination": latest.get("destination_address", "Unknown"),
                "distance": round(latest.get("route_distance_km", 0), 1),
                "eta": round(latest.get("route_eta_mins", 0), 1),
                "delay": round(latest.get("traffic_delay_mins", 0), 1)
            }

        # Determine status
        temp_val = 0
        rain_val = 0
        aqi_val = 0
        
        if weather:
            if "weather" in weather and weather["weather"]:
                temp_val = weather["weather"]["current"].get("temperature_c", 0)
                rain_val = weather["weather"]["snapshot"].get("rain_mm", 0)
            if "air_quality" in weather and weather["air_quality"]:
                aqi_val = weather["air_quality"].get("pm2_5", 0)

        # XGBoost Prediction
        prediction = predictor.predict_next_day(user.rider_id, int(temp_val))

        return {
            "rider": user.dict(),
            "wallet_balance": balance_data.get("balance_inr", 0),
            "week": {
                "label": "Last 7 Days Performance",
                "earnings": round(total_earnings, 2),
                "payout": round(total_payouts, 2),
                "premium": 82, # Plan fixed price
                "risk_score": 68,
                "triggers_fired": 2,
                "predicted_next_day": round(prediction, 2) if prediction else 0,
                "total_distance": round(total_distance, 1),
                "total_traffic_delay": round(total_traffic_delay, 1),
                "recent_route": recent_route
            },
            "environment": {
                "temperature": {"value": round(temp_val,1), "unit": "°C", "status": "warn" if temp_val > 35 else "clear", "threshold": 35},
                "rainfall": {"value": round(rain_val,1), "unit": "mm", "status": "triggered" if rain_val > 5 else "clear", "threshold": 5},
                "aqi": {"value": round(aqi_val,1), "unit": "μg/m³", "status": "warn" if aqi_val > 50 else "clear", "threshold": 50},
                "mobility": {"value": "Normal", "unit": "", "status": "clear", "threshold": "Any restriction"},
                "platform": {"value": "Online", "unit": "", "status": "clear", "threshold": "Downtime"},
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


@router.get("/earnings-chart")
async def get_earnings_chart(request: Request):
    user = require_auth(request)
    rider_data = load_history_for_rider(user.rider_id)
    
    if not rider_data:
        return {
            "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "earnings": [0]*7,
            "payouts": [0]*7,
            "expected": [800]*7,
        }
    
    # Sort history by date to ensure chronological order for the chart
    history = sorted(rider_data["history"], key=lambda x: x["date"])
    
    days = [datetime.strptime(h["date"], "%Y-%m-%d").strftime("%a") for h in history]
    earnings = [h["earnings"] for h in history]
    payouts = [h["payouts"] for h in history]
    
    return {
        "days": days,
        "earnings": earnings,
        "payouts": payouts,
        "expected": [950 for _ in range(len(history))],
    }

@router.get("/analytics")
async def get_analytics(request: Request):
    user = require_auth(request)
    rider_data = load_history_for_rider(user.rider_id)
    if not rider_data:
        raise HTTPException(status_code=404, detail="No historical data found")
    return rider_data


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
