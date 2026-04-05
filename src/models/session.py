"""
models/session.py — JWT session management + user store
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import HTTPException
import hashlib
import time
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import json
import os


# ─── Config ─────────────────────────────────────────────────────────────────

SECRET_KEY = "zero-aeon-gwi-super-secret-key-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ─── Firebase Admin Init ───────────────────────────────────────────────────

# 1. Try to get service account from environment variable (as JSON string)
# 2. Fallback to physical file
SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "gig-work-insurence-firebase-adminsdk-fbsvc-75417b9102.json")
)

try:
    if not firebase_admin._apps:
        if SERVICE_ACCOUNT_JSON:
            # Initialize from JSON string (Best for Cloud Run/GitHub)
            cred_dict = json.loads(SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase Admin initialized via Environment Variable")
        elif os.path.exists(SERVICE_ACCOUNT_PATH):
            # Initialize from local JSON file
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
            print(f"🔥 Firebase Admin initialized from {os.path.basename(SERVICE_ACCOUNT_PATH)}")
        else:
            print("⚠️ Firebase service account NOT found (no JSON env var or file). Auth will be limited.")
except Exception as e:
    print(f"❌ Error initializing Firebase Admin: {e}")

def verify_firebase_token(id_token: str) -> Optional[dict]:
    """Verify a Firebase ID token and return its claims."""
    try:
        decoded_token = firebase_auth.verify_id_token(id_token, clock_skew_seconds=10)
        return decoded_token
    except Exception as e:
        print(f"❌ Firebase token verification failed: {e}")
        return None


# ─── Database Models ─────────────────────────────────────────────────────────

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base, engine, SessionLocal

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    rider_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    zone = Column(String)
    platform = Column(String)
    weekly_plan = Column(String)
    active_since = Column(String)
    role = Column(String, default="rider")
    hashed_password = Column(String, nullable=True) # Optional if using Firebase only
    firebase_uid = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    verified_orders = Column(Integer, default=0)
    is_insured = Column(Boolean, default=False)
    
    payments = relationship("Payment", back_populates="user")
    history = relationship("RiderHistory", back_populates="user")
    hazard_reports = relationship("HazardReport", back_populates="user")

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String, primary_key=True, index=True)
    rider_id = Column(String, ForeignKey("users.rider_id"))
    amount = Column(Float)
    type = Column(String) # premium_charge, insurance_payout
    desc = Column(String)
    timestamp = Column(Float)
    date = Column(String)
    
    user = relationship("User", back_populates="payments")

class HazardReport(Base):
    __tablename__ = "hazard_reports"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rider_id = Column(String, ForeignKey("users.rider_id"))
    type = Column(String) # waterlogging, accident, closure, traffic
    lat = Column(Float)
    lon = Column(Float)
    timestamp = Column(Float)
    description = Column(String)
    
    user = relationship("User", back_populates="hazard_reports")

class RiderHistory(Base):
    __tablename__ = "rider_history"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rider_id = Column(String, ForeignKey("users.rider_id"))
    date = Column(String)
    earnings = Column(Float)
    hours_worked = Column(Float)
    weather_risk_score = Column(Integer)
    payouts = Column(Float)
    trips = Column(Integer)
    origin_address = Column(String)
    destination_address = Column(String)
    route_distance_km = Column(Float)
    route_eta_mins = Column(Float)
    traffic_delay_mins = Column(Float)
    
    user = relationship("User", back_populates="history")

# Create tables
Base.metadata.create_all(bind=engine)


# ─── Schemas (Pydantic) ──────────────────────────────────────────────────────

class SessionUser(BaseModel):
    rider_id: str
    name: str
    zone: str
    platform: str
    phone: str
    weekly_plan: str
    active_since: str
    role: str = "rider"
    firebase_uid: Optional[str] = None
    email: Optional[str] = None
    verified_orders: int = 0
    is_insured: bool = False

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    rider_id: Optional[str] = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(rider_id: str, password: str) -> Optional[User]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.rider_id == rider_id.upper()).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    finally:
        db.close()


def register_user(name: str, phone: str, zone: str, password: str) -> User:
    db = SessionLocal()
    try:
        # Generate a random ID e.g. GW-1234
        import random
        new_id = f"GW-{random.randint(1000, 9999)}"
        while db.query(User).filter(User.rider_id == new_id).first():
            new_id = f"GW-{random.randint(1000, 9999)}"
            
        db_user = User(
            rider_id=new_id,
            name=name,
            phone=phone,
            zone=zone,
            platform="Independent",
            weekly_plan="Basic Cover",
            active_since="Just now",
            hashed_password=pwd_context.hash(password),
            verified_orders=0,
            is_insured=False,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    finally:
        db.close()


def get_or_create_firebase_user(uid: str, email: str, name: str) -> User:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user:
            # Check by email as fallback
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.firebase_uid = uid
                db.commit()
                db.refresh(user)
            else:
                # Create new
                import random
                new_id = f"GW-{random.randint(1000, 9999)}"
                while db.query(User).filter(User.rider_id == new_id).first():
                    new_id = f"GW-{random.randint(1000, 9999)}"
                
                user = User(
                    rider_id=new_id,
                    name=name,
                    email=email,
                    firebase_uid=uid,
                    phone="", zone="Universal", platform="Independent",
                    weekly_plan="Basic Cover", active_since="Joined via Firebase",
                    is_insured=False,
                    verified_orders=5 # Give demo feedback immediately
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Autoseed history for new user
                seed_user_history(db, user.rider_id)
                db.commit()
        return user
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str) -> SessionUser:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        rider_id: str = payload.get("sub")
        if not rider_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.rider_id == rider_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return SessionUser.from_orm(user)
    finally:
        db.close()


def decode_token_payload(token: str) -> dict:
    """Return full JWT payload for session info page."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}


# ─── Seeding Logic ───────────────────────────────────────────────────────────



def seed_user_history(db, rider_id: str, days: int = 30):
    """Generate X days of history for a specific rider, relative to today."""
    from datetime import datetime, timedelta
    import random
    
    # Check if history already exists to avoid duplicates
    if db.query(RiderHistory).filter(RiderHistory.rider_id == rider_id).count() >= days:
        return

    # Using current date as midpoint/end point for the demo
    now = datetime.now()
    
    for i in range(days):
        current_date = now - timedelta(days=(days - 1 - i))
        date_str = current_date.strftime("%Y-%m-%d")
        is_weekend = current_date.weekday() >= 4 # Fri-Sun surge
        
        import random
        base_earnings = 600 + random.randint(0, 300)
        if is_weekend: base_earnings *= 1.3 
        
        # High risk stors
        risk = 10 + random.randint(0, 40)
        payout = 0
        if random.random() < 0.15: # 15% rainy days
            risk = 85 + random.randint(0, 10)
            payout = base_earnings * 0.4
            base_earnings -= (payout * 0.5)
        
        hist = RiderHistory(
            rider_id=rider_id,
            date=date_str,
            earnings=float(base_earnings),
            hours_worked=float(random.randint(6, 12)),
            weather_risk_score=risk,
            payouts=float(payout),
            trips=random.randint(8, 25),
            origin_address="Sector " + str(random.randint(1, 15)),
            destination_address="Point " + chr(random.randint(65, 80)),
            route_distance_km=float(random.randint(4, 18)),
            route_eta_mins=float(random.randint(15, 60)),
            traffic_delay_mins=float(random.randint(0, 15))
        )
        db.add(hist)

def seed_user_payments(db, rider_id: str):
    """Seed realistic payment records (payouts + premiums) for a demo rider."""
    from datetime import datetime, timedelta
    import random
    import uuid

    # Don't re-seed if payments already exist
    if db.query(Payment).filter(Payment.rider_id == rider_id).count() > 0:
        return

    now = datetime.now()

    # ── Insurance Payouts (parametric trigger events) ─────────────────────────
    payout_events = [
        {
            "offset_days": 25,
            "desc": "Heavy Rain Trigger — 48mm/hr detected",
            "amount": 340.0,
        },
        {
            "offset_days": 18,
            "desc": "Extreme Heat Trigger — 44°C in zone",
            "amount": 210.0,
        },
        {
            "offset_days": 11,
            "desc": "AQI Pollution Alert — PM2.5 > 300",
            "amount": 150.0,
        },
        {
            "offset_days": 5,
            "desc": "Heavy Rain Trigger — 52mm/hr detected",
            "amount": 380.0,
        },
    ]

    # Add random variation per rider so each accounts looks unique
    random.seed(hash(rider_id) % 2**31)
    for evt in payout_events:
        # Small random offset so dates differ per rider
        actual_offset = evt["offset_days"] + random.randint(-2, 2)
        evt_date = now - timedelta(days=actual_offset)
        amount = round(evt["amount"] * random.uniform(0.85, 1.15), 2)
        pay = Payment(
            id=f"PAY-{uuid.uuid4().hex[:8].upper()}",
            rider_id=rider_id,
            amount=amount,
            type="insurance_payout",
            desc=evt["desc"],
            timestamp=evt_date.timestamp(),
            date=evt_date.strftime("%Y-%m-%d"),
        )
        db.add(pay)

    # ── Weekly Premium Charges (last 4 weeks) ────────────────────────────────
    premium_amounts = [60.0, 60.0, 80.0, 60.0]  # slight variation
    for week_i, premium in enumerate(premium_amounts):
        charge_date = now - timedelta(weeks=(4 - week_i), days=1)
        charge = Payment(
            id=f"PAY-{uuid.uuid4().hex[:8].upper()}",
            rider_id=rider_id,
            amount=-premium,  # negative = charge
            type="premium_charge",
            desc=f"Weekly Premium — Micro-Insurance Plan (Week {4 - week_i})",
            timestamp=charge_date.timestamp(),
            date=charge_date.strftime("%Y-%m-%d"),
        )
        db.add(charge)


def seed_db():
    """Seed comprehensive initial riders, history, and payments for demo."""
    db = SessionLocal()
    try:
        # Seed payments for existing riders on every startup (idempotent)
        if db.query(User).count() > 0:
            for rid in ["GW-8821", "GW-4422", "GW-9901"]:
                seed_user_history(db, rid)
                seed_user_payments(db, rid)
            db.commit()
            return

        initial_users = [
            {
                "rider_id": "ADMIN-001",
                "name": "System Administrator",
                "phone": "0000000000",
                "zone": "Global Operations",
                "platform": "ShieldGig Console",
                "weekly_plan": "Admin Tier",
                "active_since": "System Launch",
                "password": "admin123",
                "role": "admin",
                "verified_orders": 5,
                "is_insured": True,
            },
            {
                "rider_id": "ADMIN-002",
                "name": "Operations Lead",
                "phone": "0000000001",
                "zone": "Regional Operations",
                "platform": "ShieldGig Console",
                "weekly_plan": "Admin Tier",
                "active_since": "Jan 2024",
                "password": "admin456",
                "role": "admin",
                "verified_orders": 5,
                "is_insured": True,
            },
            {
                "rider_id": "ADMIN-003",
                "name": "Audit Manager",
                "phone": "0000000002",
                "zone": "Compliance Dept",
                "platform": "ShieldGig Console",
                "weekly_plan": "Admin Tier",
                "active_since": "Feb 2024",
                "password": "admin789",
                "role": "admin",
                "verified_orders": 5,
                "is_insured": True,
            },
            {
                "rider_id": "GW-8821",
                "name": "Raju Kumar",
                "phone": "9876543210",
                "zone": "Bangalore Central",
                "platform": "Swiggy",
                "weekly_plan": "Micro-Insurance",
                "active_since": "Dec 2023",
                "password": "rider123",
                "role": "rider",
                "verified_orders": 5,
                "is_insured": True,
            },
            {
                "rider_id": "GW-4422",
                "name": "Priya Sharma",
                "phone": "8877665544",
                "zone": "Mumbai West",
                "platform": "Uber Eats",
                "weekly_plan": "Micro-Insurance",
                "active_since": "Jan 2024",
                "password": "rider456",
                "role": "rider",
                "verified_orders": 5,
                "is_insured": True,
            },
            {
                "rider_id": "GW-9901",
                "name": "Vikram Singh",
                "phone": "9988776655",
                "zone": "Delhi NCR",
                "platform": "Zomato",
                "weekly_plan": "Micro-Insurance",
                "active_since": "Feb 2024",
                "password": "rider789",
                "role": "rider",
                "verified_orders": 5,
                "is_insured": False,
            }
        ]

        # Seed Users
        for u in initial_users:
            if not db.query(User).filter(User.rider_id == u["rider_id"]).first():
                db_user = User(
                    rider_id=u["rider_id"],
                    name=u["name"],
                    phone=u["phone"],
                    zone=u["zone"],
                    platform=u["platform"],
                    weekly_plan=u["weekly_plan"],
                    active_since=u["active_since"],
                    hashed_password=pwd_context.hash(u["password"]),
                    role=u["role"],
                    verified_orders=u["verified_orders"],
                    is_insured=u["is_insured"],
                )
                db.add(db_user)

        # Generate history and payments for each rider
        for rid in ["GW-8821", "GW-4422", "GW-9901"]:
            seed_user_history(db, rid)
            seed_user_payments(db, rid)

        db.commit()
    finally:
        db.close()
