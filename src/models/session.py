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

# ─── Config ─────────────────────────────────────────────────────────────────

SECRET_KEY = "zero-aeon-gwi-super-secret-key-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


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
    hashed_password = Column(String)
    verified_orders = Column(Integer, default=0)
    is_insured = Column(Boolean, default=False)
    
    payments = relationship("Payment", back_populates="user")
    history = relationship("RiderHistory", back_populates="user")

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

def seed_db():
    """Seed comprehensive initial riders, history, and payments for demo."""
    db = SessionLocal()
    try:
        # 1. Seed Users (if count == 0)
        if db.query(User).count() == 0:
            initial_users = [
                {"rider_id": "ADMIN-001", "name": "System Admin", "phone": "0000000000", "zone": "HQ", "platform": "Zero-Aeon-GWI", "role": "admin", "password": "admin123", "orders": 5, "insured": True},
                {"rider_id": "GW-8821", "name": "Raju Kumar", "phone": "9876543210", "zone": "Bangalore South", "platform": "Zomato", "password": "rider123", "orders": 3, "insured": True},
                {"rider_id": "GW-4422", "name": "Priya Sharma", "phone": "9123456789", "zone": "Mumbai Central", "platform": "Swiggy", "password": "rider456", "orders": 5, "insured": True},
                {"rider_id": "GW-9901", "name": "Vikram Singh", "phone": "9988776655", "zone": "Delhi NCR", "platform": "Zomato", "password": "rider789", "orders": 0, "insured": False},
            ]
            for u in initial_users:
                db.add(User(
                    rider_id=u["rider_id"], name=u["name"], phone=u["phone"], zone=u["zone"],
                    platform=u["platform"], weekly_plan="Professional Plus", active_since="Jan 2024",
                    role=u.get("role", "rider"), hashed_password=pwd_context.hash(u["password"]),
                    verified_orders=u["orders"], is_insured=u["insured"]
                ))
            db.commit()
            print("Users seeded.")

        # 2. Seed Rider History (if count == 0)
        if db.query(RiderHistory).count() == 0:
            import random
            
            end_date = datetime.now()
            riders = ["GW-8821", "GW-4422", "GW-9901"]
            LOCS = ["Koramangala", "Indiranagar", "HSR Layout", "MG Road", "Whitefield", "Marathahalli", "BTM Layout"]
            
            for rid in riders:
                for i in range(14): # 2 weeks of history
                    day = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
                    
                    # Raju (8821) is stable (Higher earnings, consistent hours, low risk)
                    # Priya (4422) is volatile (Random swings, high risk zone)
                    if rid == "GW-8821":
                        earn = 1200 + random.randint(-100, 100)
                        hrs = 8.5 + random.uniform(-0.5, 0.5)
                        risk = random.randint(10, 30)
                    elif rid == "GW-4422":
                        earn = 800 + random.randint(-400, 600)
                        hrs = 6.0 + random.uniform(-2, 4)
                        risk = random.randint(40, 90)
                    else:
                        earn = 950 + random.randint(-200, 200)
                        hrs = 7.0 + random.uniform(-1, 1)
                        risk = random.randint(20, 60)
                        
                    payout = 0.0
                    # Occasional 'automated' trigger simulated in history
                    if risk > 80 and random.random() > 0.5:
                        payout = float(random.randint(200, 500))
                        db.add(Payment(
                            id=f"PAY-{rid}-{i}", rider_id=rid, amount=payout,
                            type="insurance_payout", desc="Parametric Trigger: Heavy Rain (Simulated Payout)",
                            timestamp=datetime.now().timestamp() - (i * 86400),
                            date=day
                        ))

                    orig = random.choice(LOCS)
                    dest = random.choice([l for l in LOCS if l != orig])
                    dist = 4.0 + random.uniform(2, 12)
                    
                    db.add(RiderHistory(
                        rider_id=rid, date=day, earnings=float(earn), hours_worked=float(hrs),
                        weather_risk_score=risk, payouts=payout, trips=random.randint(8, 22),
                        origin_address=f"{orig}, Bangalore", destination_address=f"{dest}, Bangalore",
                        route_distance_km=round(dist, 1), route_eta_mins=round(dist * 2.5 + 5, 1),
                        traffic_delay_mins=round(random.uniform(2, 15), 1)
                    ))
            db.commit()
            print("History seeded.")
    finally:
        db.close()
