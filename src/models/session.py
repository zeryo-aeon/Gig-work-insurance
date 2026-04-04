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

from sqlalchemy import Column, String, Integer, Boolean, DateTime
from models.database import Base, engine, SessionLocal

class User(Base):
    __tablename__ = "users"

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
    """Seed initial riders if not present."""
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
        
        initial_users = [
            {
                "rider_id": "ADMIN-001",
                "name": "System Admin",
                "phone": "0000000000",
                "zone": "HQ",
                "platform": "Zero-Aeon-GWI",
                "weekly_plan": "N/A",
                "active_since": "Jan 2024",
                "role": "admin",
                "password": "admin123",
                "verified_orders": 5,
                "is_insured": True,
            },
            {
                "rider_id": "GW-8821",
                "name": "Raju Kumar",
                "phone": "9876543210",
                "zone": "Bangalore South",
                "platform": "Zomato",
                "weekly_plan": "Micro-Insurance",
                "active_since": "Jan 2024",
                "password": "rider123",
                "verified_orders": 2,
                "is_insured": False,
            },
            {
                "rider_id": "GW-4422",
                "name": "Priya Sharma",
                "phone": "9123456789",
                "zone": "Mumbai Central",
                "platform": "Swiggy",
                "weekly_plan": "Hazard Multiplier",
                "active_since": "Mar 2024",
                "password": "rider456",
                "verified_orders": 5,
                "is_insured": True,
            },
            {
                "rider_id": "GW-9901",
                "name": "Vikram Singh",
                "phone": "9988776655",
                "zone": "Delhi NCR",
                "platform": "Zomato",
                "weekly_plan": "Stability Contract",
                "active_since": "Nov 2023",
                "password": "rider789",
                "verified_orders": 0,
                "is_insured": False,
            },
        ]
        
        for u in initial_users:
            db_user = User(
                rider_id=u["rider_id"],
                name=u["name"],
                phone=u["phone"],
                zone=u["zone"],
                platform=u["platform"],
                weekly_plan=u["weekly_plan"],
                active_since=u["active_since"],
                role=u["role"],
                hashed_password=pwd_context.hash(u["password"]),
                verified_orders=u["verified_orders"],
                is_insured=u["is_insured"],
            )
            db.add(db_user)
        
        db.commit()
    finally:
        db.close()
