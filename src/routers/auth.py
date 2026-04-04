"""
routers/auth.py — Login, Logout, Token endpoints
"""

from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from datetime import timedelta

from models.session import (
    authenticate_user, create_access_token,
    get_current_user, decode_token_payload,
    register_user, get_or_create_firebase_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from pydantic import BaseModel
from utils.logger import app_logger

router = APIRouter()


class FirebaseAuthRequest(BaseModel):
    uid: str
    email: str
    name: str


@router.post("/login")
async def login(
    request: Request,
    rider_id: str = Form(...),
    password: str = Form(...)
):
    """Authenticate rider and set JWT cookie."""
    user = authenticate_user(rider_id.strip(), password.strip())
    if not user:
        app_logger.warning(f"AUTH: Failed login attempt for Rider ID: {rider_id}")
        # Return error — frontend reads this JSON
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Rider ID or password"}
        )

    app_logger.info(f"AUTH: Successful login for {user.name} ({user.rider_id}) - Role: {user.role}")
    token = create_access_token(
        data={"sub": user.rider_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    redirect_url = "/admin" if user.role == "admin" else "/dashboard"
    
    response = JSONResponse(content={
        "success": True,
        "rider_id": user.rider_id,
        "name": user.name,
        "redirect": redirect_url
    })
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response


@router.post("/signup")
async def signup(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    zone: str = Form(...),
    password: str = Form(...)
):
    """Register a new rider and set JWT cookie."""
    app_logger.info(f"AUTH: New signup request - Name: {name}, Phone: {phone}")
    user = register_user(name.strip(), phone.strip(), zone.strip(), password.strip())
    
    app_logger.info(f"AUTH: Created new user account: {user.rider_id}")
    token = create_access_token(
        data={"sub": user.rider_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = JSONResponse(content={
        "success": True,
        "rider_id": user.rider_id,
        "name": user.name,
        "redirect": "/dashboard"
    })
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response


@router.post("/firebase-login")
async def firebase_login(data: FirebaseAuthRequest):
    """Bridge Firebase UID/Email with a local JWT session."""
    app_logger.info(f"AUTH: Firebase login attempt for {data.email} ({data.uid})")
    
    user = get_or_create_firebase_user(data.uid, data.email, data.name)
    
    token = create_access_token(
        data={"sub": user.rider_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    redirect_url = "/admin" if user.role == "admin" else "/dashboard"
    
    response = JSONResponse(content={
        "success": True,
        "rider_id": user.rider_id,
        "name": user.name,
        "redirect": redirect_url
    })
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response


@router.post("/logout")
async def logout():
    """Clear session cookie."""
    app_logger.info("AUTH: POST logout - Clearing session")
    response = JSONResponse(content={"success": True, "redirect": "/login"})
    response.delete_cookie("access_token")
    return response


@router.get("/logout")
async def logout_get():
    """GET logout for convenience."""
    app_logger.info("AUTH: GET logout - Redirecting to login")
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response


@router.get("/me")
async def get_me(request: Request):
    """Return current session user info."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = get_current_user(token)
    return user


@router.get("/session-data")
async def session_data(request: Request):
    """Return full JWT payload + user data for session info page."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = get_current_user(token)
    payload = decode_token_payload(token)
    
    import datetime as dt
    exp_ts = payload.get("exp", 0)
    iat_ts = payload.get("iat", 0)
    
    return {
        "user": user.dict(),
        "token_info": {
            "issued_at": dt.datetime.utcfromtimestamp(iat_ts).strftime("%Y-%m-%d %H:%M:%S UTC") if iat_ts else "—",
            "expires_at": dt.datetime.utcfromtimestamp(exp_ts).strftime("%Y-%m-%d %H:%M:%S UTC") if exp_ts else "—",
            "algorithm": "HS256",
            "token_type": "Bearer (HttpOnly Cookie)",
        }
    }
