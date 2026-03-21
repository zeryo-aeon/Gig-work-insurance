import json
import os
import random
import sys
from datetime import datetime, timedelta
import time

# Add parent directory to path to import apis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apis.Geoapify_ import GeoapifyWrapper

# User IDs from models/session.py
RIDERS = ["GW-8821", "GW-4422", "GW-9901"]

LOCATIONS = [
    "Koramangala, Bangalore", "Indiranagar, Bangalore", "Whitefield, Bangalore", 
    "Jayanagar, Bangalore", "Malleswaram, Bangalore", "Hebbal, Bangalore", 
    "BTM Layout, Bangalore", "Electronic City, Bangalore", "HSR Layout, Bangalore", 
    "Marathahalli, Bangalore"
]

def get_random_route(wrapper):
    origin = random.choice(LOCATIONS)
    dest = random.choice([loc for loc in LOCATIONS if loc != origin])
    
    # Try fetching real data
    lat1, lon1 = wrapper.get_coordinates(origin)
    lat2, lon2 = wrapper.get_coordinates(dest)
    
    if None in [lat1, lon1, lat2, lon2]:
        return origin, dest, round(random.uniform(5.0, 20.0), 1), round(random.uniform(15.0, 60.0), 1), round(random.uniform(0.0, 15.0), 1)

    dist_km, eta_mins = wrapper.get_route(lat1, lon1, lat2, lon2)
    if dist_km is None or eta_mins is None:
        return origin, dest, round(random.uniform(5.0, 20.0), 1), round(random.uniform(15.0, 60.0), 1), round(random.uniform(0.0, 15.0), 1)

    # Calculate theoretical time assuming 25 km/h base speed
    base_time = dist_km / (25 / 60.0) 
    
    # Add random simulated traffic delay to the base ETA
    traffic_delay = random.uniform(5.0, 35.0) 
    eta_mins += traffic_delay

    return origin, dest, round(dist_km, 1), round(eta_mins, 1), round(traffic_delay, 1)


def generate_history():
    history_db = {}
    end_date = datetime.now()
    wrapper = GeoapifyWrapper()
    
    # Let's cache coordinates locally to avoid hitting geocoding API too many times
    coord_cache = {}
    original_get_coords = wrapper.get_coordinates
    def cached_get_coords(loc):
        if loc not in coord_cache:
            coord_cache[loc] = original_get_coords(loc)
        return coord_cache[loc]
        
    wrapper.get_coordinates = cached_get_coords
    
    print("Generating route data... this may take a moment.")

    for rider_id in RIDERS:
        rider_history = []
        for i in range(7):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Realistic earnings patterns
            base_earnings = random.randint(800, 1500)
            hours = random.randint(6, 10)
            
            # Add some "disruption" days
            weather_risk = random.randint(10, 90)
            payout = 0
            if weather_risk > 70:
                base_earnings = int(base_earnings * 0.6)
                payout = random.randint(200, 500)
            
            # Get Geoapify Route Data
            origin, dest, dist_km, eta_mins, delay_mins = get_random_route(wrapper)
            
            rider_history.append({
                "date": date,
                "rider_id": rider_id,
                "earnings": float(base_earnings),
                "hours_worked": float(hours),
                "weather_risk_score": weather_risk,
                "payouts": float(payout),
                "trips": random.randint(10, 25),
                "origin_address": origin,
                "destination_address": dest,
                "route_distance_km": dist_km,
                "route_eta_mins": eta_mins,
                "traffic_delay_mins": delay_mins
            })
            
            # Small sleep to respect rate limits
            time.sleep(0.1)
            
        history_db[rider_id] = {
            "rider_id": rider_id,
            "history": rider_history
        }
    
    return history_db

def main():
    # Ensure src/data exists
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")
    
    history_file = os.path.join(data_dir, "rider_history.json")
    history_data = generate_history()
    
    with open(history_file, "w") as f:
        json.dump(history_data, f, indent=4)
    
    print(f"Generated 1 week of data with routes for {len(RIDERS)} users in {history_file}")

if __name__ == "__main__":
    main()
