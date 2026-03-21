"""
models/history.py — Schema for historical rider data
"""

from pydantic import BaseModel
from typing import List, Dict, Any

class DailyHistory(BaseModel):
    date: str
    rider_id: str
    earnings: float
    hours_worked: float
    weather_risk_score: int
    payouts: float
    trips: int
    origin_address: str = ""
    destination_address: str = ""
    route_distance_km: float = 0.0
    route_eta_mins: float = 0.0
    traffic_delay_mins: float = 0.0

class RiderHistory(BaseModel):
    rider_id: str
    history: List[DailyHistory]
