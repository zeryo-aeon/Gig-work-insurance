import requests
import os
from dotenv import load_dotenv
from typing import Optional, Tuple, List, Dict, Any

# Ensure we load .env from the root directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

try:
    from utils.logger import app_logger
except ImportError:
    import logging
    app_logger = logging.getLogger("GeoapifyWrapper")

class GeoapifyWrapper:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEOAPIFY_API_KEY")
        if not self.api_key:
            app_logger.warning("GEO: API key not found in environment.")

    def get_coordinates(self, city: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocoding: Converts city name to latitude and longitude."""
        app_logger.debug(f"GEO: Geocoding city: {city}")
        url = "https://api.geoapify.com/v1/geocode/search"
        params = {"text": city, "apiKey": self.api_key}
        try:
            res = requests.get(url, params=params)
            app_logger.debug(f"GEO: Geocoding Status: {res.status_code}")
            data = res.json()
            if "features" in data and len(data["features"]) > 0:
                coords = data["features"][0]["geometry"]["coordinates"]
                return coords[1], coords[0]  # Return lat, lon
        except Exception as e:
            app_logger.error(f"GEO: Geocoding Error: {e}")
        return None, None

    def get_route(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[Optional[float], Optional[float]]:
        """Routing: Get distance (km) and estimated time (minutes) between two points."""
        app_logger.info(f"GEO: Routing request from ({lat1}, {lon1}) to ({lat2}, {lon2})")
        url = "https://api.geoapify.com/v1/routing"
        params = {
            "waypoints": f"{lat1},{lon1}|{lat2},{lon2}",
            "mode": "drive",
            "apiKey": self.api_key
        }
        try:
            res = requests.get(url, params=params)
            app_logger.debug(f"GEO: Routing Status: {res.status_code}")
            data = res.json()
            if "features" in data and len(data["features"]) > 0:
                props = data["features"][0]["properties"]
                distance_km = props["distance"] / 1000
                time_min = props["time"] / 60
                app_logger.info(f"GEO: Route found: {distance_km:.1f} km, {time_min:.1f} min")
                return distance_km, time_min
        except Exception as e:
            app_logger.error(f"GEO: Routing Error: {e}")
        return None, None

    def get_route_matrix(self, origins: List[Tuple[float, float]], destinations: List[Tuple[float, float]]) -> Optional[Dict[str, Any]]:
        """Route Matrix: Calculate distances and times between multiple points."""
        app_logger.info(f"GEO: Matrix request for {len(origins)} sources and {len(destinations)} targets")
        url = "https://api.geoapify.com/v1/routematrix"
        body = {
            "mode": "drive",
            "sources": [{"location": [lon, lat]} for lat, lon in origins],
            "targets": [{"location": [lon, lat]} for lat, lon in destinations]
        }
        params = {"apiKey": self.api_key}
        try:
            res = requests.post(url, params=params, json=body)
            app_logger.debug(f"GEO: Matrix Status: {res.status_code}")
            return res.json()
        except Exception as e:
            app_logger.error(f"GEO: Route Matrix Error: {e}")
        return None

if __name__ == "__main__":
    wrapper = GeoapifyWrapper()
    pickup = "Bangalore"
    drop = "Chennai"

    # Step 1: Get coordinates
    lat1, lon1 = wrapper.get_coordinates(pickup)
    lat2, lon2 = wrapper.get_coordinates(drop)

    print("\n" + "=" * 60)
    print(f"📍 PICKUP: {pickup} → {lat1}, {lon1}")
    print(f"📍 DROP  : {drop} → {lat2}, {lon2}")
    print("=" * 60)

    # Check before proceeding
    if None in [lat1, lon1, lat2, lon2]:
        print("❌ Cannot proceed without valid coordinates.")
        exit()

    # Step 2: Routing
    distance, eta = wrapper.get_route(lat1, lon1, lat2, lon2)

    # Step 3: Route Matrix
    origins = [(lat1, lon1)]
    destinations = [(lat2, lon2)]
    matrix = wrapper.get_route_matrix(origins, destinations)

    print("\n" + "=" * 60)
    print("✅ FINAL OUTPUT")
    print("Distance:", distance)
    print("ETA:", eta)
    print("Matrix:", matrix)
    print("=" * 60)