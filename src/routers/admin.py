"""
routers/admin.py — Admin Dashboard API
"""

from fastapi import APIRouter, Request, HTTPException
from models.session import SessionLocal, User, Payment, HazardReport, RiderHistory
from services.prediction_service import predictor
from utils.logger import app_logger
from datetime import datetime
import time

router = APIRouter()

@router.get("/analysis/{rider_id}")
async def get_rider_analysis(rider_id: str):
    """Perform on-the-fly aggregation for weekly and zone-wise rider data."""
    db = SessionLocal()
    try:
        history = db.query(RiderHistory).filter(RiderHistory.rider_id == rider_id).order_by(RiderHistory.date.asc()).all()
        if not history:
            return {"weekly": [], "zones": []}
            
        # 1. Weekly Aggregation (Group by ISO Year/Week)
        weekly_data = {}
        for h in history:
            dt = datetime.strptime(h.date, "%Y-%m-%d")
            year, week, _ = dt.isocalendar()
            week_key = f"{year}-W{week}"
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {"earnings": 0, "trips": 0, "risk_sum": 0, "count": 0}
            
            weekly_data[week_key]["earnings"] += h.earnings
            weekly_data[week_key]["trips"] += h.trips
            weekly_data[week_key]["risk_sum"] += h.weather_risk_score
            weekly_data[week_key]["count"] += 1
            
        # 2. Zone Aggregation (Group by origin_address - sub-zones)
        zone_data = {}
        for h in history:
            zkey = h.origin_address or "Unknown"
            if zkey not in zone_data:
                zone_data[zkey] = {"earnings": 0, "trips": 0, "risk_sum": 0, "count": 0}
            
            zone_data[zkey]["earnings"] += h.earnings
            zone_data[zkey]["trips"] += h.trips
            zone_data[zkey]["risk_sum"] += h.weather_risk_score
            zone_data[zkey]["count"] += 1

        return {
            "weekly": [
                {
                    "label": k, 
                    "earnings": round(v["earnings"], 2), 
                    "trips": v["trips"], 
                    "avg_risk": round(v["risk_sum"] / v["count"], 1)
                } for k, v in weekly_data.items()
            ],
            "zones": [
                {
                    "zone": k, 
                    "earnings": round(v["earnings"], 2), 
                    "trips": v["trips"], 
                    "avg_risk": round(v["risk_sum"] / v["count"], 1)
                } for k, v in zone_data.items()
            ]
        }
    finally:
        db.close()

@router.get("/stats")
async def get_system_stats(request: Request):
    """Return top-level aggregate KPIs for the admin dashboard."""
    db = SessionLocal()
    try:
        # Only count actual riders, not other admins
        total_users = db.query(User).filter(User.role == 'rider').count()
        insured_users = db.query(User).filter(User.role == 'rider', User.is_insured == True).count()
        total_payouts = db.query(Payment).filter(Payment.type == "insurance_payout").count()
        total_payout_amount = sum(p.amount for p in db.query(Payment).filter(Payment.type == "insurance_payout").all())
        active_hazards = db.query(HazardReport).count()
        
        return {
            "total_users": total_users,
            "insured_users": insured_users,
            "total_payouts": total_payouts,
            "total_payout_amount": round(total_payout_amount, 2),
            "active_hazards": active_hazards,
            "system_health": "Healthy",
            "uptime": "99.9%"
        }
    finally:
        db.close()

@router.get("/hazards")
async def get_all_hazards(request: Request):
    """Fetch all crowdsourced hazard reports for admin review."""
    db = SessionLocal()
    try:
        hazards = db.query(HazardReport).order_by(HazardReport.timestamp.desc()).all()
        return {
            "hazards": [
                {
                    "id": h.id,
                    "rider_id": h.rider_id,
                    "type": h.type,
                    "lat": h.lat,
                    "lon": h.lon,
                    "description": h.description,
                    "timestamp": h.timestamp,
                    "date": time.strftime('%Y-%m-%d %H:%M', time.localtime(h.timestamp))
                } for h in hazards
            ]
        }
    finally:
        db.close()

@router.get("/reports/insurance")
async def get_insurance_reports():
    """Aggregate financial and spatial reports for insurance intelligence."""
    db = SessionLocal()
    try:
        # 1. Total Metrics
        total_premiums = db.query(Payment).filter(Payment.type == "premium_charge").all()
        total_payouts = db.query(Payment).filter(Payment.type == "insurance_payout").all()
        
        premium_sum = sum(abs(p.amount) for p in total_premiums)
        payout_sum = sum(p.amount for p in total_payouts)
        
        # 2. Zone Analysis (Join Payment with User to get zones)
        # We'll aggregate payouts by zone
        payouts_by_zone = {}
        premiums_by_zone = {}
        
        # Get all riders zone map
        riders = db.query(User).filter(User.role == 'rider').all()
        zone_map = {r.rider_id: r.zone for r in riders}
        
        for p in total_payouts:
            zone = zone_map.get(p.rider_id, "Unknown")
            payouts_by_zone[zone] = payouts_by_zone.get(zone, 0) + p.amount
            
        for p in total_premiums:
            zone = zone_map.get(p.rider_id, "Unknown")
            premiums_by_zone[zone] = premiums_by_zone.get(zone, 0) + abs(p.amount)
            
        # Format zone rankings
        zone_rankings = []
        all_zones = set(list(payouts_by_zone.keys()) + list(premiums_by_zone.keys()))
        for z in all_zones:
            zone_rankings.append({
                "zone": z,
                "payouts": round(payouts_by_zone.get(z, 0), 2),
                "premiums": round(premiums_by_zone.get(z, 0), 2),
                "ratio": round(payouts_by_zone.get(z, 0) / premiums_by_zone.get(z, 1), 2) if premiums_by_zone.get(z, 0) > 0 else 0
            })
            
        return {
            "financials": {
                "total_premiums": round(premium_sum, 2),
                "total_payouts": round(payout_sum, 2),
                "loss_ratio": round(payout_sum / premium_sum, 2) if premium_sum > 0 else 0
            },
            "zone_rankings": sorted(zone_rankings, key=lambda x: x["payouts"], reverse=True)
        }
    finally:
        db.close()

@router.get("/users")
async def get_all_users(request: Request):
    """Return all riders in the system (excluding admins)."""
    app_logger.info("ADMIN: Fetching all registered riders")
    users_list = []
    db = SessionLocal()
    try:
        # Filter to only show riders, not other admins
        users = db.query(User).filter(User.role == 'rider').all()
        for user in users:
            # Exclude password hashes for safety
            safe_data = {
                "rider_id": user.rider_id,
                "name": user.name,
                "phone": user.phone,
                "zone": user.zone,
                "platform": user.platform,
                "weekly_plan": user.weekly_plan,
                "active_since": user.active_since,
                "is_insured": user.is_insured,
                "verified_orders": user.verified_orders,
                "status": "Active" # Mock status
            }
            users_list.append(safe_data)
    finally:
        db.close()
    
    return {"users": users_list}

@router.get("/model-metrics")
async def get_model_metrics(request: Request, rider_id: str):
    """Return X-Y line points of Actual vs Predicted earnings for the XGBoost model."""
    app_logger.info(f"ADMIN: Fetching XGBoost metrics for rider {rider_id}")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.rider_id == rider_id).first()
        if not user:
            app_logger.warning(f"ADMIN: Rider {rider_id} not found for metrics request")
            raise HTTPException(status_code=404, detail="Rider not found")
    finally:
        db.close()
        
    metrics = predictor.get_model_performance(rider_id)
    return metrics

@router.get("/payments")
async def get_payments(request: Request):
    """Fetch all persistent mock payment transactions for admin view from DB."""
    app_logger.info("ADMIN: Fetching all payment transactions from database")
    db = SessionLocal()
    try:
        payments = db.query(Payment).order_by(Payment.timestamp.desc()).all()
        # Convert to list of dicts for frontend
        payment_list = [
            {
                "id": p.id,
                "rider_id": p.rider_id,
                "amount": p.amount,
                "type": p.type,
                "desc": p.desc,
                "timestamp": p.timestamp,
                "date": p.date
            } for p in payments
        ]
        return {"payments": payment_list}
    except Exception as e:
        app_logger.error(f"ADMIN: Error querying payments from DB: {e}")
        return {"payments": []}
    finally:
        db.close()

@router.get("/claims")
async def get_all_claims(request: Request):
    """Return dynamic claims derived from insurance payouts in the database."""
    app_logger.info("ADMIN: Fetching dynamic claims from payout logs")
    db = SessionLocal()
    try:
        # Get insurance payouts to represent as claims
        payouts = db.query(Payment).filter(Payment.type == "insurance_payout").order_by(Payment.timestamp.desc()).all()
        
        claims = []
        for p in payouts:
            claims.append({
                "id": f"CLM-{p.id[-4:]}",
                "rider": p.rider_id,
                "type": "Parametric",
                "trigger": p.desc.split(":")[1].split("(")[0].strip() if ":" in p.desc else "Weather",
                "benefit": f"₹{p.amount}",
                "status": "Paid",
                "date": p.date
            })
        
        # Add a few static pending ones for UI demo context if pool is empty
        if not claims:
            claims = [
                 {"id": "CLM-MOCK1", "rider": "Raju Kumar", "type": "Weather", "trigger": "Heavy Rain", "benefit": "₹340", "status": "Paid", "date": "2024-04-01"},
                 {"id": "CLM-MOCK2", "rider": "Priya Sharma", "type": "Weather", "trigger": "Extreme Heat", "benefit": "₹210", "status": "Pending", "date": "2024-04-02"},
            ]
            
        return {"claims": claims}
    finally:
        db.close()

@router.get("/policies")
async def get_all_policies(request: Request):
    """Return all active insurance policies for admin management derived from DB."""
    app_logger.info("ADMIN: Fetching dynamic insurance policies from DB")
    db = SessionLocal()
    try:
        # Get all riders (excluding admins) who have an active weekly plan or are insured
        users = db.query(User).filter(User.role == 'rider', User.weekly_plan != "None").all()
        
        policies = []
        for u in users:
            policies.append({
                "id": f"POL-{u.rider_id[-4:]}",
                "rider": u.name,
                "plan": u.weekly_plan,
                "premium": "₹60/wk" if "Micro" in u.weekly_plan else "₹120/wk" if "Premium" in u.weekly_plan else "₹45/wk",
                "coverage": "₹50,000" if "Micro" in u.weekly_plan else "₹1,50,000" if "Premium" in u.weekly_plan else "₹30,000",
                "status": "Active" if u.is_insured else "Pending"
            })
        
        return {"policies": policies}
    finally:
        db.close()
