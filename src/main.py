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

from routers import auth, dashboard, insurance, triggers, claims
from models.session import get_current_user, SessionUser

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
