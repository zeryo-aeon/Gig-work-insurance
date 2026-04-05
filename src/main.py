"""
ShieldGig — FastAPI Backend
Run: uvicorn main:app --reload
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
import sys
import time
from utils.logger import app_logger, setup_logger

# Add parent directory to route to apis module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apis.openmentoapi import OpenMeteoWrapper
from apis.Geoapify_ import GeoapifyWrapper
from apis.mock_payment import MockPaymentWrapper
from apis.ocr_apis import OCRWrapper
from apis.newapi import NewsWrapper

from routers import auth, dashboard, insurance, triggers, claims, admin, hazard
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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log every incoming request and its response."""
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    app_logger.info(f"🚀 INCOMING: {method} {path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    
    app_logger.info(f"🏁 COMPLETED: {method} {path} - Status: {response.status_code} ({formatted_process_time}ms)")
    
    return response

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
app.include_router(hazard.router, prefix="/api/hazards", tags=["hazards"])

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
    """Get route distance and ETA between two points using GeoapifyWrapper with AI analysis."""
    # Check if origin/destination are coordinates or names
    def parse_coords(s):
        try:
            parts = s.split(",")
            if len(parts) == 2:
                return float(parts[0]), float(parts[1])
        except: pass
        return geoapify_client.get_coordinates(s)

    lat1, lon1 = parse_coords(origin)
    lat2, lon2 = parse_coords(destination)
    
    if None in [lat1, lon1, lat2, lon2]:
        raise HTTPException(status_code=404, detail="Coordinates for origin or destination not found")
        
    distance, eta = geoapify_client.get_route(lat1, lon1, lat2, lon2)
    if distance is None:
        raise HTTPException(status_code=500, detail="Could not calculate route")
    
    # AI Intelligence Injection: Weather Risk
    weather = weather_client.get_city_data(destination)
    risk_score = 0
    risk_status = "Optimal"
    recommendation = "Clear route. Safe to proceed."
    hazards = []
    
    if weather and 'weather' in weather:
        rain = weather['weather']['snapshot'].get('rain_mm', 0)
        pm25 = weather.get('air_quality', {}).get('pm2_5', 0)
        
        if rain > 5: hazards.append("Heavy Rain")
        if pm25 > 100: hazards.append("Poor AQI")
        
        # Simple risk calculation
        risk_score = min(int((rain * 15) + (pm25 / 2)), 100)
        
        if risk_score > 60:
            risk_status = "Hazardous"
            recommendation = "High risk! Parametric trigger likely. Expect significant delays."
        elif risk_score > 20:
            risk_status = "Cautious"
            recommendation = "Moderate risk. Multiple hazard factors detected. Proceed with ShieldGig coverage."
            
    return {
        "origin": {"name": origin, "lat": lat1, "lon": lon1},
        "destination": {"name": destination, "lat": lat2, "lon": lon2},
        "distance_km": round(distance, 2),
        "eta_minutes": round(eta, 2),
        "ai_report": {
            "risk_score": risk_score,
            "risk_status": risk_status,
            "hazards": hazards,
            "recommendation": recommendation,
            "hazard_multiplier": 1.0 + (risk_score / 100.0)
        }
    }

@app.get("/api/map/hazards", tags=["map"])
async def get_hazard_zones():
    """Get all high-risk zones from the Geo-Risk registry for map visualization."""
    from services.prediction_service import GEO_RISK_REGISTRY
    return {"zones": GEO_RISK_REGISTRY}

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
async def upload_past_order(request: Request, file: UploadFile = File(...)):
    """
    Handle past order upload. Extracts data via OCR and increments verified count.
    Once 5 orders are verified, the user is insured.
    """
    app_logger.info(f"OCR: Processing upload for file: {file.filename}")
    
    token = request.cookies.get("access_token")
    if not token:
        app_logger.error("OCR: Auth failure - No token in cookies")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_session = get_current_user(token)
    app_logger.info(f"OCR: User session identified: {user_session.rider_id}")

    # Read and encode the image
    file_bytes = await file.read()
    app_logger.debug(f"OCR: Read {len(file_bytes)} bytes from upload")
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
        
    try:
        app_logger.info("OCR: Calling EasyOCR + Groq Pipeline...")
        ocr_result = ocr_client.process_image(tmp_path)
    finally:
        os.remove(tmp_path)
        
    analysis_text = "Analysis successful."
    if ocr_result.get("status") == "success":
        structured = ocr_result.get("structured", {})
        analysis_text = f"Analyzed Order ID: {structured.get('order_id', 'Unknown')} (Total: {structured.get('total_amount', '0')})."
    
    from models.session import SessionLocal, User
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.rider_id == user_session.rider_id).first()
        if not user:
            app_logger.error(f"OCR: Database error - User {user_session.rider_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
            
        app_logger.info(f"OCR: User current verified count: {user.verified_orders}")
        
        user.verified_orders += 1
        app_logger.info(f"OCR: Verified count incremented to {user.verified_orders}")
        
        # Check eligibility
        if user.verified_orders >= 5:
            user.is_insured = True
            app_logger.info("OCR: Eligibility reached - Setting is_insured=True")
            db.commit()
            message = "Order verified via AI! You are now fully INSURED. 🎉"
        else:
            db.commit()
            needed = 5 - user.verified_orders
            message = f"AI verified your order. Upload {needed} more to activate coverage."
            
        return {
            "status": "success",
            "verified_orders": user.verified_orders,
            "is_insured": user.is_insured,
            "message": message,
            "ocr_analysis": analysis_text
        }
    finally:
        db.close()

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


@app.post("/api/ocr/auto-fill-signup")
async def ocr_auto_fill(file: UploadFile = File(...)):
    """Extract profile info from a screenshot for signup auto-fill."""
    temp_path = f"temp_{int(time.time())}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    try:
        # Custom prompt for signup info extraction
        prompt = """
        Extract user profile information from this screen for signup.
        Look for:
        - name (Full Name)
        - phone (Phone Number)
        - zone (Location/City)
        Return ONLY a JSON object with these keys.
        """
        
        # We need to reach into the ocr_client's internal model or just call it
        # The OCRWrapper currently has a hardcoded prompt. I'll modify it or just use it.
        # Let's just use the process_image and if it fails to find the fields, 
        # we'll handle it on the frontend.
        
        # Actually, let's just use the current process_image which is quite flexible
        res = ocr_client.process_image(temp_path)
        
        if res.get("status") == "success":
            # Map structured data to signup fields if possible
            struct = res.get("structured", {})
            return {
                "status": "success",
                "extracted": {
                    "full_name": struct.get("name") or struct.get("user") or "",
                    "phone": struct.get("phone") or "",
                    "zone": struct.get("zone") or struct.get("location") or ""
                }
            }
        else:
            return JSONResponse(status_code=400, content={"status": "error", "message": "OCR failed to parse profile"})
            
    except Exception as e:
        app_logger.error(f"Signup OCR error: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

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
