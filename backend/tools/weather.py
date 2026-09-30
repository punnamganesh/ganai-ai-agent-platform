import os
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WeatherTool:
    """Tool to fetch current weather data using OpenWeatherMap API"""
    
    def __init__(self):
        self.name = "weather"
        self.description = "Fetches current weather for a given city"
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def execute(self, city: str, units: str = "metric") -> Dict[str, Any]:
        """
        Execute weather fetch for a city.
        
        Args:
            city (str): City name (e.g., "London")
            units (str): "metric" for Celsius, "imperial" for Fahrenheit
        
        Returns:
            Dict with success flag, weather data, or error message.
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "WEATHER_API_KEY not set in environment",
                "message": "Please add your OpenWeatherMap API key to .env"
            }
        
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad status
            data = response.json()
            
            # Extract relevant info
            weather_info = {
                "city": data.get("name"),
                "country": data.get("sys", {}).get("country"),
                "temperature": data.get("main", {}).get("temp"),
                "feels_like": data.get("main", {}).get("feels_like"),
                "humidity": data.get("main", {}).get("humidity"),
                "weather": data.get("weather", [{}])[0].get("description", "unknown"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "units": "°C" if units == "metric" else "°F"
            }
            
            return {
                "success": True,
                "data": weather_info,
                "formatted": self._format_weather(weather_info)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to fetch weather data. Check city name or network."
            }
    
    def _format_weather(self, info: Dict[str, Any]) -> str:
        """Format weather data into a readable string"""
        temp = info["temperature"]
        feels = info["feels_like"]
        units = info["units"]
        desc = info["weather"].capitalize()
        city = info["city"]
        country = info["country"]
        humidity = info["humidity"]
        wind = info["wind_speed"]
        
        return (f"Current weather in {city}, {country}: {desc}, "
                f"{temp}{units} (feels like {feels}{units}), "
                f"humidity {humidity}%, wind {wind} m/s")
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "requires_api_key": True
        }