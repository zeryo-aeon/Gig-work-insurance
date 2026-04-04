from fastapi import APIRouter, Request, HTTPException
import os
import sys
from datetime import datetime

# Add root to path for apis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apis.openmentoapi import OpenMeteoWrapper
from apis.mock_payment import MockPaymentWrapper

from models.session import get_current_user
from utils.logger import app_logger

router = APIRouter()
weather_client = OpenMeteoWrapper()
payment_client = MockPaymentWrapper()


def require_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_current_user(token)


@router.get("/live")
async def get_live_triggers(request: Request):
    user = require_auth(request)
    zone = user.zone if user.zone != "HQ" else "Bangalore"
    app_logger.info(f"TRIGGERS: Fetching LIVE triggers for rider {user.rider_id} in {zone}")
    
    # Fetch real weather data
    weather_data = weather_client.get_city_data(zone)
    if not weather_data:
        weather_data = weather_client.get_city_data("Bangalore") # Fallback

    curr_temp = weather_data['weather']['current']['temperature_c']
    curr_rain = weather_data['weather']['snapshot']['rain_mm']
    curr_aqi = weather_data['air_quality']['pm2_5']
    
    # Define Triggers logic
    triggers = []
    
    # 1. Heavy Rain
    rain_triggered = curr_rain > 5.0 # mm/hr threshold for demo
    triggers.append({
        "id": "rain",
        "name": "Heavy Rain (Parametric)",
        "icon": "🌧️",
        "source": f"Open-Meteo · {zone}",
        "current_value": f"{curr_rain} mm/hr",
        "threshold": "> 5.0 mm/hr",
        "percent": min(100, int((curr_rain / 5.0) * 100)),
        "bar_color": "warn" if rain_triggered else "blue",
        "status": "triggered" if rain_triggered else "clear",
        "payout": "₹340" if rain_triggered else "—",
        "payout_amount": 340 if rain_triggered else 0,
    })

    # 2. Extreme Heat
    heat_triggered = curr_temp > 38.0
    triggers.append({
        "id": "heat",
        "name": "Extreme Heat (Health Risk)",
        "icon": "🌡️",
        "source": "Open-Meteo · Heat index",
        "current_value": f"{curr_temp}°C",
        "threshold": "> 38°C",
        "percent": min(100, int((curr_temp / 38.0) * 100)),
        "bar_color": "gold" if heat_triggered else "green",
        "status": "triggered" if heat_triggered else ("watch" if curr_temp > 35 else "clear"),
        "payout": "₹220" if heat_triggered else "—",
        "payout_amount": 220 if heat_triggered else 0,
    })

    # 3. Water Logging (Hyper-local Simulation)
    # Triggered if Safe Zone is False AND rain > threshold
    from services.prediction_service import GEO_RISK_REGISTRY
    zone_risk = GEO_RISK_REGISTRY.get(user.zone, {"water_logging_safe": False})
    flood_triggered = not zone_risk["water_logging_safe"] and curr_rain > 2.0
    
    triggers.append({
        "id": "flood",
        "name": "Water Logging (Geo-Risk)",
        "icon": "🚦",
        "source": f"ShieldGig Risk Map · {user.zone}",
        "current_value": "Critical Accumulation" if flood_triggered else "Safe",
        "threshold": "Zone Risk + Rain",
        "percent": 100 if flood_triggered else (50 if curr_rain > 1.0 else 0),
        "bar_color": "warn" if flood_triggered else "green",
        "status": "triggered" if flood_triggered else "clear",
        "payout": "₹450" if flood_triggered else "—",
        "payout_amount": 450 if flood_triggered else 0,
    })

    # 4. Air Quality (AQI)
    aqi_triggered = curr_aqi > 100.0 # Standard threshold
    triggers.append({
        "id": "aqi",
        "name": "Air Pollution (AQI)",
        "icon": "💨",
        "source": "Open-Meteo · PM2.5",
        "current_value": f"{curr_aqi} AQI",
        "threshold": "> 100 AQI",
        "percent": min(100, int((curr_aqi / 100.0) * 100)),
        "bar_color": "purple" if aqi_triggered else "green",
        "status": "triggered" if aqi_triggered else "clear",
        "payout": "₹150" if aqi_triggered else "—",
        "payout_amount": 150 if aqi_triggered else 0,
    })

    # 5. Platform Demand Crash (Simulated Platform API)
    import random
    demand_drop = random.randint(10, 60)
    demand_triggered = demand_drop > 40
    triggers.append({
        "id": "demand",
        "name": "Market Demand Crash",
        "icon": "📉",
        "source": "Mock Gig-Platform API",
        "current_value": f"{demand_drop}% Drop",
        "threshold": "> 40% Drop",
        "percent": demand_drop,
        "bar_color": "warn" if demand_triggered else "blue",
        "status": "triggered" if demand_triggered else "clear",
        "payout": "₹500" if demand_triggered else "—",
        "payout_amount": 500 if demand_triggered else 0,
    })

    # Automated "Zero-Touch" Payout Logic
    # In a real app, this would check if a payout was already made today for this trigger
    active_count = sum(1 for t in triggers if t["status"] == "triggered")
    if active_count > 0:
        for t in triggers:
            if t["status"] == "triggered":
                # Simulated Payout call
                app_logger.info(f"ZERO-TOUCH: Automatically processing payout for {user.rider_id} - Trigger: {t['name']}")
                payment_client.process_payout(user.rider_id, t["payout_amount"], f"Automated Payout: {t['name']}")

    return {
        "active_count": active_count,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "triggers": triggers
    }
