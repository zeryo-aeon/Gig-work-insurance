"""
routers/claims.py — Claims history API
"""

from fastapi import APIRouter, Request, HTTPException
from models.session import get_current_user

router = APIRouter()


def require_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_current_user(token)


@router.get("/summary")
async def get_claims_summary(request: Request):
    require_auth(request)
    return {
        "month": "June 2025",
        "total_paid": 1840,
        "total_triggers": 7,
        "premiums_paid": 240,
        "net_benefit": 1600,
    }


@router.get("/history")
async def get_claims_history(request: Request):
    require_auth(request)
    return {
        "claims": [
            {
                "id": "CLM-007",
                "icon": "🌧️",
                "title": "Heavy Rain Trigger",
                "detail": "June 22, 2025 · 48mm/hr · Queued",
                "amount": 340,
                "status": "queued",
            },
            {
                "id": "CLM-006",
                "icon": "🌧️",
                "title": "Heavy Rain Trigger",
                "detail": "June 18, 2025 · 52mm/hr · Paid",
                "amount": 380,
                "status": "paid",
            },
            {
                "id": "CLM-005",
                "icon": "🌡️",
                "title": "Extreme Heat Trigger",
                "detail": "June 15, 2025 · 44°C · Paid",
                "amount": 260,
                "status": "paid",
            },
            {
                "id": "CLM-004",
                "icon": "🚫",
                "title": "Zone Curfew — Strike",
                "detail": "June 10, 2025 · Full day · Paid",
                "amount": 480,
                "status": "paid",
            },
            {
                "id": "CLM-003",
                "icon": "🌡️",
                "title": "Extreme Heat Trigger",
                "detail": "June 8, 2025 · 43°C · Paid",
                "amount": 220,
                "status": "paid",
            },
            {
                "id": "CLM-002",
                "icon": "💨",
                "title": "High AQI Trigger",
                "detail": "June 5, 2025 · AQI 320 · Paid",
                "amount": 160,
                "status": "paid",
            },
        ]
    }
