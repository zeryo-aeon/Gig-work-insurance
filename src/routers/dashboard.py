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
from apis.mock_payment import MockPaymentWrapper
from services.prediction_service import predictor
import json
from utils.logger import app_logger
from models.database import SessionLocal
from models.session import RiderHistory

def load_history_for_rider(rider_id: str):
    """Load historical earnings and risk data from database."""
    db = SessionLocal()
    try:
        history = db.query(RiderHistory).filter(RiderHistory.rider_id == rider_id).order_by(RiderHistory.date.desc()).all()
        if not history:
            return None
        
        # Convert to the original dict format expected by the frontend
        return {
            "rider_id": rider_id,
            "history": [
                {
                    "date": h.date,
                    "earnings": h.earnings,
                    "hours_worked": h.hours_worked,
                    "weather_risk_score": h.weather_risk_score,
                    "payouts": h.payouts,
                    "trips": h.trips,
                    "origin_address": h.origin_address,
                    "destination_address": h.destination_address,
                    "route_distance_km": h.route_distance_km,
                    "route_eta_mins": h.route_eta_mins,
                    "traffic_delay_mins": h.traffic_delay_mins
                } for h in history
            ]
        }
    finally:
        db.close()

router = APIRouter()
weather_client = OpenMeteoWrapper()
payment_client = MockPaymentWrapper()


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

        # AI Dynamic Pricing Logic (XGBoost + Geo-Risk)
        pricing_data = predictor.calculate_premium_modifier(user.rider_id, zone=user.zone, current_weather_risk=int(temp_val))
        
        # Calculate dynamic premium to display on dashboard
        dynamic_base = 30 - pricing_data.get("discount_applied", 0)
        computed_premium = float(max(5.0, round((dynamic_base * pricing_data.get("modifier", 1.0)) / 5) * 5))
        
        # Determine risk level for dashboard display
        risk_score = pricing_data.get("points_total", 0)
        # Normalize -50 to 50 into 0-100 for display, lower is better usually but let's stick to 0-100 high=bad
        display_risk = max(0, min(100, 50 - risk_score)) 
        
        return {
            "rider": user.dict(),
            "wallet_balance": balance_data.get("balance_inr", 0),
            "pricing": pricing_data,
            "week": {
                "label": "Last 7 Days Performance",
                "earnings": round(total_earnings, 2),
                "payout": round(total_payouts, 2),
                "premium": computed_premium, 
                "risk_score": display_risk,
                "triggers_fired": 1 if total_payouts > 0 else 0,
                "predicted_next_day": pricing_data["modifier"] * 500, # scaling factor for demo
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
            },
            "verified_orders": user.verified_orders,
            "is_insured": user.is_insured,
            "trips_today": random.randint(0, 4) if user.is_insured else 0,
            "payout_eligible": user.is_insured
        }
    except Exception as e:
        app_logger.error(f"DASHBOARD: Error fetching summary for rider {user.rider_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e


@router.get("/earnings-chart")
async def get_earnings_chart(request: Request):
    user = require_auth(request)
    app_logger.info(f"DASHBOARD: Fetching earnings chart for rider {user.rider_id}")
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
    app_logger.info(f"DASHBOARD: Fetching full analytics for rider {user.rider_id}")
    rider_data = load_history_for_rider(user.rider_id)
    if not rider_data:
        app_logger.warning(f"DASHBOARD: No historical data found for rider {user.rider_id}")
        raise HTTPException(status_code=404, detail="No historical data found")
    return rider_data


@router.get("/risk-factors")
async def get_risk_factors(request: Request):
    user = require_auth(request)
    # Fetch real live weather data for risk calculation
    user_zone = user.dict().get("zone", "Bangalore")
    weather = weather_client.get_city_data(user_zone)
    temp_val = 0
    if weather and "weather" in weather and weather["weather"]:
        temp_val = weather["weather"]["current"].get("temperature_c", 0)
    
    pricing_data = predictor.calculate_premium_modifier(user.rider_id, zone=user.zone, current_weather_risk=int(temp_val))
    
    # Map points to dashboard factors
    risk_score = pricing_data.get("points_total", 0)
    display_risk = max(0, min(100, 50 - risk_score))
    
    factors = [
        {"name": "Weather Risk", "score": min(100, int(temp_val * 2)), "color": "warn" if temp_val > 30 else "green"},
        {"name": "Zone Hazard", "score": 100 if not pricing_data.get("is_safe_zone") else 20, "color": "warn" if not pricing_data.get("is_safe_zone") else "green"},
        {"name": "Income Stability", "score": 100 if risk_score < 0 else 30, "color": "gold" if risk_score < 10 else "green"},
        {"name": "Activity Level", "score": 50, "color": "gold"},
    ]
    
    return {
        "overall_score": display_risk,
        "level": "High" if display_risk > 60 else "Moderate" if display_risk > 30 else "Low",
        "factors": factors
    }


@router.get("/disruptions")
async def get_disruptions(request: Request):
    user = require_auth(request)
    # Fetch real live weather data
    user_zone = user.dict().get("zone", "Bangalore")
    weather = weather_client.get_city_data(user_zone)
    
    rain_val = 0
    temp_val = 0
    if weather and "weather" in weather and weather["weather"]:
        temp_val = weather["weather"]["current"].get("temperature_c", 0)
        rain_val = weather["weather"]["snapshot"].get("rain_mm", 0)

    # Historical data for payouts
    rider_data = load_history_for_rider(user.rider_id)
    total_payouts = sum(h["payouts"] for h in rider_data["history"]) if rider_data else 0

    return {
        "disruptions": [
            {
                "name": "Heavy Rain",
                "type": "Environmental",
                "icon": "🌧️",
                "measured": f"{rain_val} mm/hr",
                "threshold": "> 5 mm/hr",
                "loss": f"₹{int(total_payouts/2)}" if total_payouts > 0 else "—",
                "status": "triggered" if rain_val > 5 else "clear"
            },
            {
                "name": "Extreme Heat",
                "type": "Environmental",
                "icon": "🌡️",
                "measured": f"{temp_val}°C",
                "threshold": "> 35°C",
                "loss": "—",
                "status": "warn" if temp_val > 35 else "clear"
            },
            {
                "name": "Air Pollution",
                "type": "Environmental",
                "icon": "💨",
                "measured": "Normal",
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
                "measured": "Stable",
                "threshold": "< 5 orders/hr",
                "loss": "—",
                "status": "clear"
            },
        ]
    }
