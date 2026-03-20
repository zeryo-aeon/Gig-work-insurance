# Gig-work-insurance

## Risk Assessment
![Risk](riskassement.png)

## Saving Buffer
![Buffer](savingbuffer.png)


# Persona: Food Delivery Partner (Zomato / Swiggy)

- Works 8–12 hours daily
- Earns ~₹20K–₹30K/month depending on demand
- Income depends on

    - Orders/hour    
    - Working hours
    - External conditions

Key reality:
> If they **cannot work → income = 0**

#  DISRUPTION TABLE 

## Environmental Disruptions (Primary Layer)

| Disruption Type | Example        | Measurable Parameter             | Impact (Income Loss)                       |
| --------------- | -------------- | -------------------------------- | ------------------------------------------ |
| Extreme Heat    | 42°C+ heatwave | Temperature, Heat Index          | Rider reduces working hours → ↓ deliveries |
| Heavy Rain      | Monsoon bursts | Rainfall (mm/hr)                 | Order cancellations + slower delivery      |
| Floods          | Urban flooding | Govt alerts / rainfall threshold | Zero deliveries in affected zone           |
| Pollution       | AQI > 300      | AQI API                          | Health discomfort → reduced shifts         |

👉 Insight:  
Gig workers **adapt in real-time (reduce hours)** → direct income drop

## Social Disruptions (Mobility Layer)

| Disruption Type | Example          | Measurable Parameter   | Impact                |
| --------------- | ---------------- | ---------------------- | --------------------- |
| Curfew          | Govt restriction | Zone lockdown flag     | 100% income loss      |
| Strikes         | Transport strike | Mobility index drop    | Partial/zero delivery |
| Zone Closure    | Political rally  | Geo-fenced restriction | No pickup/drop        |

## Platform Disruptions 

| Disruption Type | Example             | Measurable Parameter | Impact                  |
| --------------- | ------------------- | -------------------- | ----------------------- |
| Demand Crash    | Low orders          | Orders/hour ↓ 40%    | Lower earnings          |
| App Downtime    | Server crash        | API failure logs     | No orders               |
| Supply Chain    | Restaurant shutdown | Active restaurants ↓ | Earnings drop up to 50% |


# AI/ML models
Here’s your **refined version (AI added inside weekly pricing, title unchanged)**

# WEEKLY PRICING MODELS

## 1️ Baseline + Event Guarantee

- **Model:** Minimum weekly income (e.g., ₹2500) if active hours met
- **Trigger:** Disruption → hours counted as worked
- **Outcome:** Income stability without forcing risky work    

## 2️ Micro-Insurance (5% Deduction Model)

- **Model:** 5% of weekly earnings → Resilience Pool (+ platform match)
- **Trigger:** Weather/event → automatic payout    
- **Outcome:** Self-sustained parametric insurance fund

##  3️ Hazard Multiplier Pay
 
- **Model:** 1.5× base pay during Hazard Days
- **Trigger:** Heat / rain threshold crossed
- **Outcome:** Compensates risk instead of relying on surge pricing    

## 4️ Tiered Stability Contracts

- **Model:** Fixed weekly schedule → guaranteed income floor
- **Trigger:** Curfew / lockdown → 70% payout    
- **Outcome:** Predictable weekly earnings

# AI / ML MODELS (SEPARATE)

- **Income Prediction:** XGBoost → predicts weekly earnings    
- **Risk Prediction:** Random Forest → predicts disruption probability
- **Fraud Detection:** Isolation Forest → detects fake claims
- **Loss Estimation:** Regression → calculates income loss %

#  PARAMETRIC TRIGGERS (SEPARATE)

- Rainfall > threshold → payout
- Temperature > threshold → payout
- AQI > threshold → payout    
- Curfew / zone closure → payout

# WEEKLY PRICING LOGIC (SEPARATE)

👉 AI dynamically adjusts pricing based on risk + income patterns

```id="4kw5vy"
Weekly Premium = Base + (AI Risk Score × Coverage Level × Income Variability)
```

### AI Inputs:

- Weather forecast (Open-Meteo)
- Location risk (Geoapify)
- Historical earnings pattern

### Example:

- Low risk → ₹30/week
- Medium risk → ₹60/week
- High risk → ₹100/week