import xgboost as xgb
import pandas as pd
import numpy as np
import json
import os
from typing import Dict, Any, Optional, List

# --- Geo-Risk Registry (Simulated Hyper-local Risk Database) ---
GEO_RISK_REGISTRY = {
    "Bangalore South": {"water_logging_safe": True, "risk_score": 1, "avg_disruption_hrs": 2},
    "Koramangala": {"water_logging_safe": True, "risk_score": 1, "avg_disruption_hrs": 3},
    "Indiranagar": {"water_logging_safe": False, "risk_score": 3, "avg_disruption_hrs": 8},
    "Whitefield": {"water_logging_safe": False, "risk_score": 4, "avg_disruption_hrs": 12},
    "Mumbai Central": {"water_logging_safe": False, "risk_score": 5, "avg_disruption_hrs": 15},
    "Delhi NCR": {"water_logging_safe": True, "risk_score": 2, "avg_disruption_hrs": 5},
    "HQ": {"water_logging_safe": True, "risk_score": 0, "avg_disruption_hrs": 0},
}

class IncomePredictor:
    def __init__(self, history_file: str):
        self.history_file = history_file
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            objective='reg:squarederror'
        )
        self.is_trained = False

    def _load_history(self) -> Dict[str, Any]:
        if not os.path.exists(self.history_file):
            return {}
        with open(self.history_file, 'r') as f:
            return json.load(f)

    def train_for_rider(self, rider_id: str):
        """Train (or simulate training) a model for a specific rider based on their history."""
        data = self._load_history()
        if rider_id not in data:
            return False
        
        history = data[rider_id]['history']
        if len(history) < 3:
            return False

        df = pd.DataFrame(history)
        
        # Feature Engineering (Simple)
        df['target'] = df['earnings'].shift(-1) # Predict next day's earnings
        df = df.dropna()
        
        if df.empty:
            return False

        X = df[['earnings', 'hours_worked', 'weather_risk_score']]
        y = df['target']
        
        self.model.fit(X, y)
        self.is_trained = True
        return True

    def predict_next_day(self, rider_id: str, current_weather_risk: int) -> Optional[float]:
        """Predict tomorrow's earnings for the rider."""
        data = self._load_history()
        if rider_id not in data:
            return None
        
        history = data[rider_id]['history']
        # Take the most recent day as features for the prediction (simplified)
        latest = history[0] # assuming history is sorted desc
        
        if not self.is_trained:
            success = self.train_for_rider(rider_id)
            if not success:
                # Fallback to a simple average if training fails or data is sparse
                return sum(h['earnings'] for h in history) / len(history)

        X_input = pd.DataFrame([{
            'earnings': latest['earnings'],
            'hours_worked': latest['hours_worked'],
            'weather_risk_score': current_weather_risk
        }])
        
        prediction = self.model.predict(X_input)
        return float(prediction[0])

    def calculate_premium_modifier(self, rider_id: str, zone: str = "Unknown", current_weather_risk: int = 0) -> Dict[str, Any]:
        """
        Calculates dynamic points, modifier, and AI insights.
        Returns: {modifier, final_premium, discount_applied, points_total, points_breakdown, insights, is_safe_zone}
        """
        predicted_earnings = self.predict_next_day(rider_id, current_weather_risk)
        
        # Base modifier calculation
        data = self._load_history()
        history = data.get(rider_id, {}).get('history', [])
        
        avg_earnings = sum(h['earnings'] for h in history) / len(history) if history else 500
        avg_hours = sum(h['hours_worked'] for h in history) / len(history) if history else 20
        
        if avg_earnings == 0: avg_earnings = 500
            
        ratio = predicted_earnings / avg_earnings if predicted_earnings is not None else 1.0
        
        # Volatility factor
        volatility_modifier = 1.0 + abs(1.0 - ratio) * 0.4
        volatility_modifier = max(1.0, min(1.5, volatility_modifier))

        # --- Unified Risk Tone Engine (Directional Consistency) ---
        points_breakdown = []
        raw_points = 0
        
        # 1. Evaluate All Risk/Trust Factors
        # Safe Zone Factor
        risk_info = GEO_RISK_REGISTRY.get(zone, {"water_logging_safe": False, "risk_score": 3})
        if risk_info["water_logging_safe"]:
            raw_points += 15
        else:
            raw_points -= 10
            
        # Activity Factor
        if avg_hours > 30:
            raw_points += 10
        elif avg_hours < 15:
            raw_points -= 15
            
        # Stability Factor
        if len(history) > 3:
            earnings_var = np.std([h['earnings'] for h in history]) / avg_earnings
            if earnings_var < 0.2:
                raw_points += 20
            elif earnings_var > 0.5:
                raw_points -= 20

        # Volatility Factor (from Prediction ratio)
        if ratio < 0.7:
            raw_points -= 25
        elif ratio > 0.95:
            raw_points += 10

        # 2. Determine UNIFIED DIRECTION
        # If raw_points > 0, we are in "Incentive Mode"
        # If raw_points <= 0, we are in "Penalty Mode"
        is_positive_mode = raw_points > 0
        total_points = 0
        
        if is_positive_mode:
            # Only include positive points
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
            
            # Force Modifier to be at or below baseline
            volatility_modifier = max(0.85, min(1.0, 1.0 - (total_points / 200)))
        else:
            # Only include negative points
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

            # Force Modifier to be at or above baseline
            volatility_modifier = max(1.05, min(1.6, 1.0 + abs(total_points / 100)))

        # Pts to Discount: 1 pt = ₹0.5
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
            coverage_hours_bonus = 8 # Extra protection in high risk mode
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
        """
        Generates data for an X-Y line chart showing predictions vs actual outcomes over time.
        """
        data = self._load_history()
        if rider_id not in data or len(data[rider_id]['history']) < 3:
            return {"dates": [], "actual": [], "predicted": []}

        # Ensure historical order
        history = sorted(data[rider_id]['history'], key=lambda x: x["date"])
        df = pd.DataFrame(history)
        
        if not self.is_trained:
            self.train_for_rider(rider_id)

        dates = []
        actual = []
        predicted = []

        # Generate X-Y line points (Target next day vs Actual next day)
        for i in range(len(df) - 1):
            row_today = df.iloc[i]
            row_tomorrow = df.iloc[i+1] # The day we are predicting

            date_str = pd.to_datetime(row_tomorrow['date']).strftime('%b %d')
            weather_risk = row_today.get('weather_risk_score', 0)
            
            if self.is_trained:
                X_input = pd.DataFrame([{
                    'earnings': row_today['earnings'],
                    'hours_worked': row_today['hours_worked'],
                    'weather_risk_score': weather_risk
                }])
                pred = float(self.model.predict(X_input)[0])
            else:
                pred = row_today['earnings']

            dates.append(date_str)
            actual.append(row_tomorrow['earnings'])
            predicted.append(round(pred, 2))

        return {
            "dates": dates,
            "actual": actual,
            "predicted": predicted
        }

# Singleton instance for the app
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
predictor = IncomePredictor(os.path.join(DATA_DIR, "rider_history.json"))
