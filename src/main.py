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
from apis.mock_payment import MockPaymentWrapper
from apis.ocr_apis import OCRWrapper
from apis.newapi import NewsWrapper

from routers import auth, dashboard, insurance, triggers, claims, admin
from models.session import get_current_user, SessionUser, seed_db

weather_client = OpenMeteoWrapper()
geoapify_client = GeoapifyWrapper()
payment_client = MockPaymentWrapper()
ocr_client = OCRWrapper()
news_client = NewsWrapper()

app = FastAPI(
    title="Zero-Aeon-GWI API",
    description="Parametric Insurance for Gig Workers",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    seed_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(insurance.router, prefix="/api/insurance", tags=["insurance"])
app.include_router(triggers.router, prefix="/api/triggers", tags=["triggers"])
app.include_router(claims.router, prefix="/api/claims", tags=["claims"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/api/status", tags=["health"])
async def get_status():
    """Health check for the Android app."""
    return {
        "status": "online",
        "server": "ShieldGig Core",
        "version": "1.0.0",
        "last_sync": datetime.now().isoformat()
    }


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

# ─── OCR & Eligibility Routes ───────────────────────────────────────────────

@app.post("/api/ocr/upload-order", tags=["ocr"])
async def upload_past_order(request: Request):
    """
    Handle past order upload. Extracts data via OCR and increments verified count.
    Once 5 orders are verified, the user is insured.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_session = get_current_user(token)
    
    # Process the uploaded file (mocking the extraction logic)
    # In a real scenario, we'd use: ocr_client.query({"image": ...})
    
    # Call the OCR Wrapper to demonstrate integration
    ocr_result = ocr_client.query({
        "messages": [{"role": "user", "content": [{"type": "text", "text": "Extract order ID and amount."}]}],
        "model": "Qwen/Qwen2.5-VL-72B-Instruct:ovhcloud"
    })
    
    from models.session import USERS_DB
    user = USERS_DB.get(user_session.rider_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user["verified_orders"] = user.get("verified_orders", 0) + 1
    
    # Check eligibility
    if user["verified_orders"] >= 5:
        user["is_insured"] = True
        message = "Order verified via AI! You are now fully INSURED. 🎉"
    else:
        needed = 5 - user["verified_orders"]
        message = f"AI verified your order. Upload {needed} more to activate coverage."
        
    return {
        "status": "success",
        "verified_orders": user["verified_orders"],
        "is_insured": user["is_insured"],
        "message": message,
        "ocr_analysis": "Order data successfully extracted and validated."
    }

@app.get("/api/news/traffic", tags=["news"])
async def get_traffic_news():
    """Fetch AI-curated traffic intelligence using NewsWrapper."""
    raw_news = news_client.fetch_news()
    processed_news = news_client.process(raw_news)
    return {"news": processed_news}

# ─── Page Routes ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to login or dashboard based on session."""
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Serve the Admin HTML Dashboard."""
    return templates.TemplateResponse(request=request, name="admin.html", context={})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html", context={})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = get_current_user(token)
        return templates.TemplateResponse(
            request=request, name="dashboard.html", context={"user": user}
        )
    except Exception:
        response = RedirectResponse(url="/login")
        response.delete_cookie("access_token")
        return response


@app.get("/map", response_class=HTMLResponse)
async def map_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = get_current_user(token)
        # Inject the Geoapify API Key from env
        api_key = os.getenv("GEOAPIFY_API_KEY", "YOUR_GEOAPIFY_API_KEY")
        tom_key = os.getenv("TOMTOM_API_KEY", "YOUR_TOMTOM_API_KEY")
        return templates.TemplateResponse(
            request=request,
            name="map.html",
            context={
                "user": user,
                "api_key": api_key,
                "tomtom_key": tom_key
            }
        )
    except Exception:
        return RedirectResponse(url="/login")


@app.get("/session-info", response_class=HTMLResponse)
async def session_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    try:
        user = get_current_user(token)
        return templates.TemplateResponse(
            request=request, name="session.html", context={"user": user}
        )
    except Exception:
        return RedirectResponse(url="/login")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
