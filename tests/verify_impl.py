import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from services.prediction_service import predictor
from routers.dashboard import load_history_for_rider

def verify_data_generation():
    print("--- Verifying Data Generation ---")
    RIDERS = ["GW-8821", "GW-4422", "GW-9901"]
    for rider_id in RIDERS:
        data = load_history_for_rider(rider_id)
        if not data:
            print(f"❌ No data for {rider_id}")
            return False
        history = data.get("history", [])
        if len(history) != 7:
            print(f"❌ Expected 7 days of history for {rider_id}, found {len(history)}")
            return False
        print(f"✅ Found 7 days of history for {rider_id}")
    return True

def verify_prediction():
    print("\n--- Verifying XGBoost Prediction ---")
    RIDERS = ["GW-8821", "GW-4422", "GW-9901"]
    for rider_id in RIDERS:
        # Mock weather risk
        weather_risk = 30
        prediction = predictor.predict_next_day(rider_id, weather_risk)
        if prediction is None or prediction <= 0:
            print(f"❌ Invalid prediction for {rider_id}: {prediction}")
            return False
        print(f"✅ Prediction for {rider_id} (tomorrow): ₹{prediction:.2f}")
    return True

if __name__ == "__main__":
    d_ok = verify_data_generation()
    p_ok = verify_prediction()
    
    if d_ok and p_ok:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
    else:
        print("\n❌ SOME VERIFICATIONS FAILED.")
        sys.exit(1)
