import xgboost as xgb
import pandas as pd
import numpy as np
import os
from typing import Dict, Any, Optional, List
from models.session import SessionLocal, RiderHistory

# --- Geo-Risk Registry (Simulated Hyper-local Risk Database) ---
GEO_RISK_REGISTRY = {
    "Bangalore South": {"lat": 12.9141, "lon": 77.5892, "water_logging_safe": True, "risk_score": 1, "avg_disruption_hrs": 2},
    "Koramangala": {"lat": 12.9352, "lon": 77.6245, "water_logging_safe": True, "risk_score": 1, "avg_disruption_hrs": 3},
    "Indiranagar": {"lat": 12.9784, "lon": 77.6408, "water_logging_safe": False, "risk_score": 3, "avg_disruption_hrs": 8},
    "Whitefield": {"lat": 12.9698, "lon": 77.7499, "water_logging_safe": False, "risk_score": 4, "avg_disruption_hrs": 12},
    "Mumbai Central": {"lat": 18.9696, "lon": 72.8193, "water_logging_safe": False, "risk_score": 5, "avg_disruption_hrs": 15},
    "Delhi NCR": {"lat": 28.6139, "lon": 77.2090, "water_logging_safe": True, "risk_score": 2, "avg_disruption_hrs": 5},
    "HQ": {"lat": 12.9716, "lon": 77.5946, "water_logging_safe": True, "risk_score": 0, "avg_disruption_hrs": 0},
}

class IncomePredictor:
    def __init__(self):
        self.models_cache = {} # Dictionary to store trained models per rider_id
        self.base_params = {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 3,
            'objective': 'reg:squarederror'
        }

    def _get_rider_history(self, rider_id: str) -> List[Dict[str, Any]]:
        """Fetch historical records for a rider from the database."""
        db = SessionLocal()
        try:
            records = db.query(RiderHistory).filter(RiderHistory.rider_id == rider_id).order_by(RiderHistory.date.desc()).all()
            return [
                {
                    "earnings": r.earnings,
                    "hours_worked": r.hours_worked,
                    "weather_risk_score": r.weather_risk_score,
                    "date": r.date
                } for r in records
            ]
        finally:
            db.close()

    def train_for_rider(self, rider_id: str):
        """Train a model for a specific rider and store it in cache."""
        history = self._get_rider_history(rider_id)
        if len(history) < 3:
            return False

        df = pd.DataFrame(history)
        df = df.sort_values('date')
        
        df['target'] = df['earnings'].shift(-1)
        df = df.dropna()
        
        if df.empty:
            return False

        X = df[['earnings', 'hours_worked', 'weather_risk_score']]
        y = df['target']
        
        model = xgb.XGBRegressor(**self.base_params)
        model.fit(X, y)
        self.models_cache[rider_id] = model
        return True

    def predict_next_day(self, rider_id: str, current_weather_risk: int) -> Optional[float]:
        """Predict tomorrow's earnings for the rider using their specific model."""
        history = self._get_rider_history(rider_id)
        if not history:
            return None
        
        latest = history[0]
        
        # Ensure we have a model for this rider
        if rider_id not in self.models_cache:
            success = self.train_for_rider(rider_id)
            if not success:
                return sum(h['earnings'] for h in history) / len(history)

        model = self.models_cache[rider_id]
        X_input = pd.DataFrame([{
            'earnings': latest['earnings'],
            'hours_worked': latest['hours_worked'],
            'weather_risk_score': current_weather_risk
        }])
        
        prediction = model.predict(X_input)
        return float(prediction[0])

    def calculate_premium_modifier(self, rider_id: str, zone: str = "Unknown", current_weather_risk: int = 0) -> Dict[str, Any]:
        """Calculates dynamic points, modifier, and AI insights."""
        predicted_earnings = self.predict_next_day(rider_id, current_weather_risk)
        
        history = self._get_rider_history(rider_id)
        avg_earnings = sum(h['earnings'] for h in history) / len(history) if history else 500
        avg_hours = sum(h['hours_worked'] for h in history) / len(history) if history else 20
        
        if avg_earnings == 0: avg_earnings = 500
        ratio = predicted_earnings / avg_earnings if predicted_earnings is not None else 1.0
        
        # Volatility factor
        volatility_modifier = 1.0 + abs(1.0 - ratio) * 0.4
        volatility_modifier = max(1.0, min(1.5, volatility_modifier))

        points_breakdown = []
        raw_points = 0
        
        risk_info = GEO_RISK_REGISTRY.get(zone, {"water_logging_safe": False, "risk_score": 3})
        if risk_info["water_logging_safe"]:
            raw_points += 15
        else:
            raw_points -= 10
            
        if avg_hours > 30:
            raw_points += 10
        elif avg_hours < 15:
            raw_points -= 15
            
        if len(history) > 3:
            earnings_var = np.std([h['earnings'] for h in history]) / avg_earnings
            if earnings_var < 0.2:
                raw_points += 20
            elif earnings_var > 0.5:
                raw_points -= 20

        if ratio < 0.7:
            raw_points -= 25
        elif ratio > 0.95:
            raw_points += 10

        is_positive_mode = raw_points > 0
        total_points = 0
        
        if is_positive_mode:
            if risk_info["water_logging_safe"]:
                total_points += 15
                points_breakdown.append({"name": "Safe Zone Bonus", "points": 15, "type": "positive"})
            if avg_hours > 30:
                total_points += 10
                points_breakdown.append({"name": "High Activity Reward", "points": 10, "type": "positive"})
            if len(history) > 3 and (np.std([h['earnings'] for h in history]) / avg_earnings) < 0.2:
                total_points += 20
                points_breakdown.append({"name": "Stability Incentive", "points": 20, "type": "positive"})
            if ratio > 0.95:
                total_points += 10
                points_breakdown.append({"name": "Predictive Stability Bonus", "points": 10, "type": "positive"})
            
            volatility_modifier = max(0.85, min(1.0, 1.0 - (total_points / 200)))
        else:
            if not risk_info["water_logging_safe"] or risk_info["risk_score"] >= 4:
                total_points -= 20
                points_breakdown.append({"name": "High Risk Zone Penalty", "points": -20, "type": "negative"})
            if avg_hours < 15:
                total_points -= 15
                points_breakdown.append({"name": "Low Activity Penalty", "points": -15, "type": "negative"})
            if ratio < 0.7:
                total_points -= 25
                points_breakdown.append({"name": "High Volatility Penalty", "points": -25, "type": "negative"})
            if len(history) > 3 and (np.std([h['earnings'] for h in history]) / avg_earnings) > 0.4:
                total_points -= 10
                points_breakdown.append({"name": "Historical Variance Penalty", "points": -10, "type": "negative"})

            volatility_modifier = max(1.05, min(1.6, 1.0 + abs(total_points / 100)))

        discount = total_points * 0.5 
        
        insights = []
        if is_positive_mode:
            insights.append(f"Excellent trust score! All dynamic factors are trending towards savings.")
            if total_points > 30: insights.append(f"You've reached 'Elite' status. Premium significantly reduced.")
        else:
            insights.append("Risk levels are elevated. All dynamic factors are adjusting to protect your income buffer.")
            insights.append("Consider shifts in safe zones to unlock trust incentives.")
        
        coverage_hours_bonus = 0
        if not is_positive_mode:
            coverage_hours_bonus = 8
            insights.append(f"Alert: High risk detected. ShieldGig has auto-extended protection by +{coverage_hours_bonus}hrs.")
        
        return {
            "modifier": float(volatility_modifier),
            "points_total": total_points,
            "points_breakdown": points_breakdown,
            "discount_applied": float(discount),
            "coverage_hours_bonus": coverage_hours_bonus,
            "insights": insights,
            "is_safe_zone": risk_info["water_logging_safe"]
        }

    def get_model_performance(self, rider_id: str) -> Dict[str, list]:
        """Generates performance data for the rider using their specific model."""
        history = self._get_rider_history(rider_id)
        if len(history) < 3:
            return {"dates": [], "actual": [], "predicted": []}

        history = sorted(history, key=lambda x: x["date"])
        df = pd.DataFrame(history)
        
        if rider_id not in self.models_cache:
            self.train_for_rider(rider_id)

        model = self.models_cache.get(rider_id)
        dates = []
        actual = []
        predicted = []

        for i in range(len(df) - 1):
            row_today = df.iloc[i]
            row_tomorrow = df.iloc[i+1]

            date_str = pd.to_datetime(row_tomorrow['date']).strftime('%b %d')
            weather_risk = row_today.get('weather_risk_score', 0)
            
            if model:
                X_input = pd.DataFrame([{
                    'earnings': row_today['earnings'],
                    'hours_worked': row_today['hours_worked'],
                    'weather_risk_score': weather_risk
                }])
                pred = float(model.predict(X_input)[0])
            else:
                pred = row_today['earnings']

            dates.append(date_str)
            actual.append(row_tomorrow['earnings'])
            predicted.append(round(pred, 2))

        last_actual = actual[-1] if actual else 0
        last_pred = predicted[-1] if predicted else 0
        diff_pct = ((last_pred - last_actual) / last_actual * 100) if last_actual > 0 else 0
        
        narrative = f"Prediction for next period: ₹{last_pred}. "
        if diff_pct < -5:
            narrative += f"AI detects a potential {abs(round(diff_pct))}% income dip. Higher local weather risk is likely impacting this corridor."
        elif diff_pct > 5:
            narrative += f"Growth trend of {round(diff_pct)}% detected! Optimal conditions and platform demand are favoring this rider's current route choice."
        else:
            narrative += "Stable income patterns detected. Model confidence is high due to consistent historical performance."

        return {
            "dates": dates,
            "actual": actual,
            "predicted": predicted,
            "tell": narrative
        }

predictor = IncomePredictor()

