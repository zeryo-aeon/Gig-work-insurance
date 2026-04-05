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
    from models.database import SessionLocal
    from models.session import Payment
    from routers.insurance import PLANS
    import random
    from datetime import date

    active_count = sum(1 for t in triggers if t["status"] == "triggered")
    
    if active_count > 0 and user.is_insured:
        db = SessionLocal()
        try:
            # 1. Per day max 1 trigger cap
            today_str = date.today().strftime("%Y-%m-%d")
            payouts_today = db.query(Payment).filter(
                Payment.rider_id == user.rider_id, 
                Payment.date == today_str,
                Payment.type == "insurance_payout"
            ).count()
            
            if payouts_today == 0:
                # 2. Simulate or fetch ability to deliver (Trips < 3)
                # In a real app, we would query the current day's live orders.
                # Here we simulate with a random chance or specific logic.
                mock_trips_today = random.randint(0, 5) 
                
                if mock_trips_today < 3:
                    # 3. Get pricing model multiplier
                    # Default coverage base level is 1.0 (e.g. Basic Plan)
                    coverage_multiplier = 1.0 
                    
                    # Fetch plan directly via plan's string name (or ID if mapped differently, e.g. "Micro-Insurance" could just mean any plan from plans list, but let's just pick one based on `weekly_plan` if available)
                    # We will do a generic lookup or default based on PLANS
                    plan_info = next((p for p in PLANS if p["name"].lower() == user.weekly_plan.lower() or p["id"] == user.weekly_plan.lower()), PLANS[0])
                    coverage_multiplier = plan_info.get("coverage_level", 1.0)

                    # Trigger the first active alert
                    for t in triggers:
                        if t["status"] == "triggered":
                            # Calculate final payout
                            final_amount = t["payout_amount"] * coverage_multiplier
                            
                            app_logger.info(f"ZERO-TOUCH: Automatically processing payout for {user.rider_id} - Trigger: {t['name']} (Trips: {mock_trips_today}, Multiplier: {coverage_multiplier}x, Paid out: {final_amount})")
                            
                            payment_client.process_payout(user.rider_id, final_amount, f"Automated Payout: {t['name']}")
                            
                            # Log to Database so we don't trigger again today
                            import uuid
                            new_pay = Payment(
                                id=f"PAY-{uuid.uuid4().hex[:8].upper()}",
                                rider_id=user.rider_id,
                                amount=final_amount,
                                type="insurance_payout",
                                desc=f"Automated Payout: {t['name']} (Weather Triggered, Trips: {mock_trips_today})",
                                timestamp=datetime.utcnow().timestamp(),
                                date=today_str,
                            )
                            db.add(new_pay)
                            db.commit()
                            
                            # Break out to ensure only ONE trigger is paid out
                            break
        finally:
            db.close()

    return {
        "active_count": active_count,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "triggers": triggers
    }
