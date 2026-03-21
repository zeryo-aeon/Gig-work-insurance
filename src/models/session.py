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

SECRET_KEY = "shieldgig-super-secret-key-change-in-production-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ─── Schemas ─────────────────────────────────────────────────────────────────

class SessionUser(BaseModel):
    rider_id: str
    name: str
    zone: str
    platform: str
    phone: str
    weekly_plan: str
    active_since: str


class TokenData(BaseModel):
    rider_id: Optional[str] = None


# ─── Mock User DB ─────────────────────────────────────────────────────────────

USERS_DB = {
    "GW-8821": {
        "rider_id": "GW-8821",
        "name": "Raju Kumar",
        "phone": "9876543210",
        "zone": "Bangalore South",
        "platform": "Zomato",
        "weekly_plan": "Micro-Insurance",
        "active_since": "Jan 2024",
        # password: rider123
        "hashed_password": pwd_context.hash("rider123"),
    },
    "GW-4422": {
        "rider_id": "GW-4422",
        "name": "Priya Sharma",
        "phone": "9123456789",
        "zone": "Mumbai Central",
        "platform": "Swiggy",
        "weekly_plan": "Hazard Multiplier",
        "active_since": "Mar 2024",
        # password: rider456
        "hashed_password": pwd_context.hash("rider456"),
    },
    "GW-9901": {
        "rider_id": "GW-9901",
        "name": "Vikram Singh",
        "phone": "9988776655",
        "zone": "Delhi NCR",
        "platform": "Zomato",
        "weekly_plan": "Stability Contract",
        "active_since": "Nov 2023",
        # password: rider789
        "hashed_password": pwd_context.hash("rider789"),
    },
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(rider_id: str, password: str) -> Optional[dict]:
    user = USERS_DB.get(rider_id.upper())
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def register_user(name: str, phone: str, zone: str, password: str) -> dict:
    # Generate a random ID e.g. GW-1234
    import random
    new_id = f"GW-{random.randint(1000, 9999)}"
    while new_id in USERS_DB:
        new_id = f"GW-{random.randint(1000, 9999)}"
        
    user_doc = {
        "rider_id": new_id,
        "name": name,
        "phone": phone,
        "zone": zone,
        "platform": "Independent",
        "weekly_plan": "Basic Cover",
        "active_since": "Just now",
        "hashed_password": pwd_context.hash(password),
    }
    USERS_DB[new_id] = user_doc
    return user_doc

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

    user = USERS_DB.get(rider_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return SessionUser(
        rider_id=user["rider_id"],
        name=user["name"],
        zone=user["zone"],
        platform=user["platform"],
        phone=user["phone"],
        weekly_plan=user["weekly_plan"],
        active_since=user["active_since"],
    )


def decode_token_payload(token: str) -> dict:
    """Return full JWT payload for session info page."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}
