"""
routers/triggers.py — Live parametric triggers API
"""

from fastapi import APIRouter, Request, HTTPException
from models.session import get_current_user

router = APIRouter()


def require_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_current_user(token)


@router.get("/live")
async def get_live_triggers(request: Request):
    require_auth(request)
    return {
        "active_count": 2,
        "last_updated": "2025-06-22T14:32:00Z",
        "triggers": [
            {
                "id": "rain",
                "name": "Heavy Rain (Rainfall Threshold)",
                "icon": "🌧️",
                "source": "Open-Meteo API · Zone: Bangalore South",
                "current_value": "48 mm/hr",
                "threshold": "> 30 mm/hr",
                "percent": 100,
                "bar_color": "warn",
                "status": "triggered",
                "payout": "₹340",
                "payout_amount": 340,
            },
            {
                "id": "heat",
                "name": "Extreme Heat (Heat Index)",
                "icon": "🌡️",
                "source": "Open-Meteo · Heat index calc",
                "current_value": "38°C",
                "threshold": "> 42°C",
                "percent": 72,
                "bar_color": "gold",
                "status": "watch",
                "payout": "—",
                "payout_amount": 0,
            },
            {
                "id": "aqi",
                "name": "Air Pollution (AQI Threshold)",
                "icon": "💨",
                "source": "AQICN API · PM2.5 index",
                "current_value": "142 AQI",
                "threshold": "> 300 AQI",
                "percent": 47,
                "bar_color": "green",
                "status": "clear",
                "payout": "—",
                "payout_amount": 0,
            },
            {
                "id": "flood",
                "name": "Urban Flood / Govt Alert",
                "icon": "🚦",
                "source": "NDMA API · Flood zone overlay",
                "current_value": "No Alert",
                "threshold": "Any flood alert",
                "percent": 0,
                "bar_color": "warn",
                "status": "clear",
                "payout": "—",
                "payout_amount": 0,
            },
            {
                "id": "curfew",
                "name": "Curfew / Zone Lockdown",
                "icon": "🚫",
                "source": "Geoapify + manual govt flag",
                "current_value": "No Curfew",
                "threshold": "Zone lockdown flag",
                "percent": 0,
                "bar_color": "warn",
                "status": "clear",
                "payout": "—",
                "payout_amount": 0,
            },
            {
                "id": "demand",
                "name": "Platform Demand Crash",
                "icon": "📉",
                "source": "Zomato/Swiggy mock API · orders/hr",
                "current_value": "8 orders/hr",
                "threshold": "Drop > 40% baseline",
                "percent": 35,
                "bar_color": "blue",
                "status": "clear",
                "payout": "—",
                "payout_amount": 0,
            },
        ]
    }
