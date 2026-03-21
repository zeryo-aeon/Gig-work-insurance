import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import requests
from typing import Optional, Dict, Any, Tuple

class OpenMeteoWrapper:
    def __init__(self, cache_expire: int = 3600, retries: int = 5, backoff_factor: float = 0.2):
        """Initialize the OpenMeteo wrapper with caching and retry logic."""
        self.cache_session = requests_cache.CachedSession('.cache', expire_after=cache_expire)
        self.retry_session = retry(self.cache_session, retries=retries, backoff_factor=backoff_factor)
        self.openmeteo = openmeteo_requests.Client(session=self.retry_session)

    def get_coordinates(self, city: str) -> Tuple[Optional[float], Optional[float]]:
        """Get the latitude and longitude for a given city."""
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": city, "count": 1}
        try:
            res = requests.get(url, params=params).json()
            if "results" in res and res["results"]:
                r = res["results"][0]
                return float(r["latitude"]), float(r["longitude"])
        except Exception:
            pass
        return None, None

    def get_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch current and hourly weather data for the given coordinates."""
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "wind_speed_10m"],
            "hourly": ["temperature_2m", "rain", "windspeed_10m"]
        }

        responses = self.openmeteo.weather_api(
            "https://api.open-meteo.com/v1/forecast",
            params=weather_params
        )
        weather_res = responses[0]

        # Current weather
        current = weather_res.Current()
        current_temp = current.Variables(0).Value()
        current_wind = current.Variables(1).Value()
        current_time_str = pd.to_datetime(current.Time(), unit="s", utc=True).strftime('%Y-%m-%d %H:%M:%S UTC')

        # Hourly weather snapshot
        hourly = weather_res.Hourly()
        temp = hourly.Variables(0).ValuesAsNumpy()[0]
        rain = hourly.Variables(1).ValuesAsNumpy()[0]
        wind = hourly.Variables(2).ValuesAsNumpy()[0]

        return {
            "current": {
                "temperature_c": round(float(current_temp), 1),
                "wind_speed_kmh": round(float(current_wind), 1),
                "time": current_time_str
            },
            "snapshot": {
                "temperature_c": round(float(temp), 1),
                "rain_mm": round(float(rain), 1),
                "wind_speed_kmh": round(float(wind), 1)
            }
        }

    def get_air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch hourly air quality data (PM2.5) for the given coordinates."""
        air_params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ["pm2_5"]
        }

        responses = self.openmeteo.weather_api(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params=air_params
        )
        air_res = responses[0]

        air_hourly = air_res.Hourly()
        pm25 = air_hourly.Variables(0).ValuesAsNumpy()[0]

        return {
            "pm2_5": round(float(pm25), 1)
        }

    def get_city_data(self, city: str) -> Optional[Dict[str, Any]]:
        """Fetch coordinates, weather, and air quality data for a specific city."""
        lat, lon = self.get_coordinates(city)
        if lat is None or lon is None:
            return None
            
        weather_data = self.get_weather(lat, lon)
        air_quality_data = self.get_air_quality(lat, lon)
        
        return {
            "city": city,
            "coordinates": {
                "latitude": lat,
                "longitude": lon
            },
            "weather": weather_data,
            "air_quality": air_quality_data
        }

if __name__ == "__main__":
    wrapper = OpenMeteoWrapper()
    cities = ["Bangalore", "Chennai", "Mumbai", "Delhi"]
    
    for city in cities:
        data = wrapper.get_city_data(city)
        
        if not data:
            print(f"\n❌ {city}: Not found")
            continue

        print("\n" + "="*60)
        print(f"📍 CITY: {data['city']}")
        print(f"🌍 Location: {data['coordinates']['latitude']}, {data['coordinates']['longitude']}")
        print("-" * 60)

        current = data['weather']['current']
        print("🔴 CURRENT WEATHER")
        print(f"🌡 Temperature : {current['temperature_c']}°C")
        print(f"💨 Wind Speed : {current['wind_speed_kmh']} km/h")
        print(f"⏰ Time        : {current['time']}")
        
        snapshot = data['weather']['snapshot']
        print("\n📊 WEATHER SNAPSHOT")
        print(f"🌡 Temp       : {snapshot['temperature_c']}°C")
        print(f"🌧 Rain       : {snapshot['rain_mm']} mm")
        print(f"💨 Wind       : {snapshot['wind_speed_kmh']} km/h")
        
        aq = data['air_quality']
        print("\n🌫️ AIR QUALITY")
        print(f"PM2.5 Level  : {aq['pm2_5']} µg/m³")
        print("="*60)