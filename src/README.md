# ShieldGig — Parametric Insurance for Gig Workers
## FastAPI Backend + Full Dashboard

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
uvicorn main:app --reload
```

### 3. Open in browser
```
http://localhost:8000
```

---

## 📁 Project Structure

```
shieldgig/
├── main.py                  # FastAPI app entry point
├── requirements.txt
├── models/
│   └── session.py           # JWT auth, user DB, session helpers
├── routers/
│   ├── auth.py              # Login / Logout / /me / /session-data
│   ├── dashboard.py         # Summary, chart, risk, disruptions
│   ├── insurance.py         # Plans, AI premium, activate
│   ├── triggers.py          # Live parametric triggers
│   └── claims.py            # Claims history & summary
├── templates/
│   ├── login.html           # Login page
│   ├── dashboard.html       # Main dashboard (API-connected)
│   └── session.html         # Session / account info page
└── static/                  # (place any CSS/JS/image assets here)
```

---

## 🔐 Demo Accounts

| Rider ID | Password  | Name          | Zone             |
|----------|-----------|---------------|------------------|
| GW-8821  | rider123  | Raju Kumar    | Bangalore South  |
| GW-4422  | rider456  | Priya Sharma  | Mumbai Central   |
| GW-9901  | rider789  | Vikram Singh  | Delhi NCR        |

---

## 🔌 API Endpoints

### Auth
| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| POST   | `/auth/login`         | Login (form data)              |
| POST   | `/auth/logout`        | Logout (clear cookie)          |
| GET    | `/auth/me`            | Current user info              |
| GET    | `/auth/session-data`  | Full JWT + user details        |

### Dashboard
| Method | Endpoint                        | Description             |
|--------|---------------------------------|-------------------------|
| GET    | `/api/dashboard/summary`        | KPIs + env data         |
| GET    | `/api/dashboard/earnings-chart` | Weekly bar chart data   |
| GET    | `/api/dashboard/risk-factors`   | AI risk score breakdown |
| GET    | `/api/dashboard/disruptions`    | Disruption table        |

### Insurance
| Method | Endpoint                          | Description             |
|--------|-----------------------------------|-------------------------|
| GET    | `/api/insurance/plans`            | All 4 coverage plans    |
| GET    | `/api/insurance/ai-premium`       | AI-calculated premium   |
| POST   | `/api/insurance/activate`         | Activate a plan         |

### Triggers
| Method | Endpoint              | Description              |
|--------|-----------------------|--------------------------|
| GET    | `/api/triggers/live`  | All live trigger statuses|

### Claims
| Method | Endpoint                | Description          |
|--------|-------------------------|----------------------|
| GET    | `/api/claims/summary`   | Month summary stats  |
| GET    | `/api/claims/history`   | Full payout log      |

---

## 🔒 Auth Flow

1. User POSTs Rider ID + password to `/auth/login`
2. Server verifies bcrypt password, issues JWT
3. JWT stored as **HttpOnly cookie** (XSS-safe)
4. All page routes verify cookie before serving HTML
5. All API routes verify cookie before returning data
6. `/auth/logout` clears the cookie

---

## 🛠 Tech Stack

| Layer      | Tech                          |
|------------|-------------------------------|
| Backend    | FastAPI (Python)              |
| Auth       | JWT (python-jose) + bcrypt    |
| Sessions   | HttpOnly Cookie               |
| Templates  | Jinja2                        |
| Frontend   | Vanilla JS + Fetch API        |
| Fonts      | Syne, Space Mono, DM Sans     |

---

## 🔧 Extending to Production

- Replace `USERS_DB` dict with Supabase / PostgreSQL
- Replace `SECRET_KEY` with env variable
- Add real Open-Meteo, AQI, Geoapify API calls in `routers/dashboard.py`
- Add scikit-learn / XGBoost models in `models/` for live risk scoring
- Deploy with Docker + Nginx reverse proxy
