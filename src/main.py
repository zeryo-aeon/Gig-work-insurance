"""
ShieldGig — FastAPI Backend
Run: uvicorn main:app --reload
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import uvicorn
import os
import sys

# Add parent directory to route to apis module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apis.openmentoapi import OpenMeteoWrapper
from apis.Geoapify_ import GeoapifyWrapper
from apis.mock_payment import MockPaymentSystem

from routers import auth, dashboard, insurance, triggers, claims
from models.session import get_current_user, SessionUser

weather_client = OpenMeteoWrapper()
geoapify_client = GeoapifyWrapper()
payment_client = MockPaymentSystem()

app = FastAPI(
    title="ShieldGig API",
    description="Parametric Insurance for Gig Workers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(insurance.router, prefix="/api/insurance", tags=["insurance"])
app.include_router(triggers.router, prefix="/api/triggers", tags=["triggers"])
app.include_router(claims.router, prefix="/api/claims", tags=["claims"])


# ─── Data Routes ────────────────────────────────────────────────────────────

@app.get("/api/weather", tags=["weather"])
async def get_weather(city: str = "Bangalore"):
    """Get live weather and air quality for a city using OpenMeteoWrapper."""
    data = weather_client.get_city_data(city)
    if not data:
        raise HTTPException(status_code=404, detail="Weather data not found")
    return data

@app.get("/api/route", tags=["routing"])
async def get_route(origin: str = "Bangalore", destination: str = "Chennai"):
    """Get route distance and ETA between two cities using GeoapifyWrapper."""
    lat1, lon1 = geoapify_client.get_coordinates(origin)
    lat2, lon2 = geoapify_client.get_coordinates(destination)
    if None in [lat1, lon1, lat2, lon2]:
        raise HTTPException(status_code=404, detail="Coordinates for origin or destination not found")
        
    distance, eta = geoapify_client.get_route(lat1, lon1, lat2, lon2)
    if distance is None:
        raise HTTPException(status_code=500, detail="Could not calculate route")
        
    return {
        "origin": {"city": origin, "latitude": lat1, "longitude": lon1},
        "destination": {"city": destination, "latitude": lat2, "longitude": lon2},
        "distance_km": round(distance, 2),
        "eta_minutes": round(eta, 2)
    }

@app.post("/api/payment/payout", tags=["payment"])
async def process_mock_payout(rider_id: str, amount: float, reason: str = "Automated Insurance Trigger"):
    """Trigger a mock payout to a rider's wallet."""
    return payment_client.process_payout(rider_id, amount, reason)
    
@app.get("/api/payment/balance", tags=["payment"])
async def get_wallet_balance(rider_id: str):
    """Get the mock wallet balance of a rider."""
    return payment_client.get_wallet_balance(rider_id)

# ─── Page Routes ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to login or dashboard based on session."""
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = get_current_user(token)
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user
        })
    except Exception:
        response = RedirectResponse(url="/login")
        response.delete_cookie("access_token")
        return response


@app.get("/session-info", response_class=HTMLResponse)
async def session_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = get_current_user(token)
        return templates.TemplateResponse("session.html", {
            "request": request,
            "user": user
        })
    except Exception:
        return RedirectResponse(url="/login")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
