"""
routers/hazard.py — Crowdsourced Hazard Reporting API
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from models.session import SessionLocal, HazardReport, get_current_user
from pydantic import BaseModel
import time

router = APIRouter()

class HazardReportRequest(BaseModel):
    type: str
    lat: float
    lon: float
    description: str = ""

@router.post("/report")
async def report_hazard(request: Request, report: HazardReportRequest):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_session = get_current_user(token)
    
    db = SessionLocal()
    try:
        new_report = HazardReport(
            rider_id=user_session.rider_id,
            type=report.type,
            lat=report.lat,
            lon=report.lon,
            timestamp=time.time(),
            description=report.description
        )
        db.add(new_report)
        db.commit()
        return {"status": "success", "message": "Hazard reported. Thank you for keeping the community safe!"}
    finally:
        db.close()

@router.get("/active")
async def get_active_hazards():
    """Fetch hazards from the last 4 hours."""
    db = SessionLocal()
    try:
        four_hours_ago = time.time() - (4 * 3600)
        hazards = db.query(HazardReport).filter(HazardReport.timestamp > four_hours_ago).all()
        return {
            "hazards": [
                {
                    "id": h.id,
                    "type": h.type,
                    "lat": h.lat,
                    "lon": h.lon,
                    "description": h.description,
                    "timestamp": h.timestamp,
                    "rider_id": h.rider_id
                } for h in hazards
            ]
        }
    finally:
        db.close()
