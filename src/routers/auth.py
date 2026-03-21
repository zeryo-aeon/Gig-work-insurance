"""
routers/auth.py — Login, Logout, Token endpoints
"""

from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from datetime import timedelta

from models.session import (
    authenticate_user, create_access_token,
    get_current_user, decode_token_payload,
    register_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()


@router.post("/login")
async def login(
    request: Request,
    rider_id: str = Form(...),
    password: str = Form(...)
):
    """Authenticate rider and set JWT cookie."""
    user = authenticate_user(rider_id.strip(), password.strip())
    if not user:
        # Return error — frontend reads this JSON
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Rider ID or password"}
        )

    token = create_access_token(
        data={"sub": user["rider_id"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = JSONResponse(content={
        "success": True,
        "rider_id": user["rider_id"],
        "name": user["name"],
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


@router.post("/signup")
async def signup(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    zone: str = Form(...),
    password: str = Form(...)
):
    """Register a new rider and set JWT cookie."""
    user = register_user(name.strip(), phone.strip(), zone.strip(), password.strip())
    
    token = create_access_token(
        data={"sub": user["rider_id"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = JSONResponse(content={
        "success": True,
        "rider_id": user["rider_id"],
        "name": user["name"],
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

@router.post("/logout")
async def logout():
    """Clear session cookie."""
    response = JSONResponse(content={"success": True, "redirect": "/login"})
    response.delete_cookie("access_token")
    return response


@router.get("/logout")
async def logout_get():
    """GET logout for convenience."""
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
