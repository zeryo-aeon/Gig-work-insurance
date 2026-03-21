import xgboost as xgb
import pandas as pd
import numpy as np
import json
import os
from typing import Dict, Any, Optional

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

    def calculate_premium_modifier(self, rider_id: str, current_weather_risk: int = 0) -> float:
        """
        Calculates a dynamic premium modifier based on predicted income volatility relative to average.
        Returns a factor between 1.0 (baseline) and 1.5 (high risk).
        """
        predicted_earnings = self.predict_next_day(rider_id, current_weather_risk)
        if predicted_earnings is None:
            return 1.10

        data = self._load_history()
        history = data[rider_id]['history']
        if len(history) == 0:
            return 1.10
            
        avg_earnings = sum(h['earnings'] for h in history) / len(history)

        if avg_earnings == 0:
            return 1.10
        
        ratio = predicted_earnings / avg_earnings
        
        # Volatility modifier
        modifier = 1.0 + abs(1.0 - ratio) * 0.4
        
        # Bound between 1.0 and 1.5
        return float(max(1.0, min(1.5, modifier)))

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
