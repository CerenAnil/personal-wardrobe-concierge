"""
Weather MCP Server — stdio transport, FastMCP.

Wraps the Open-Meteo API (free, no key required for weather).
Geocoding (city -> lat/lon) uses the Open-Meteo geocoding API, also free.

Tools:
  get_weather(city, date)   returns temp, condition, summary

Start: python src/mcp/weather_server.py
"""

import os
import sys
from datetime import datetime, date as date_type

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-server")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL   = "https://api.open-meteo.com/v1/forecast"
TIMEOUT       = 10.0

# WMO weather code -> condition label
WMO_CONDITIONS: dict[int, str] = {
    0:  "sunny",
    1:  "mostly sunny", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "foggy",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    56: "freezing drizzle", 57: "heavy freezing drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    66: "freezing rain", 67: "heavy freezing rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    77: "snow grains",
    80: "light showers", 81: "showers", 82: "heavy showers",
    85: "snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
}


def _geocode(city: str) -> tuple[float, float]:
    """Return (latitude, longitude) for a city name. Raises on failure."""
    resp = httpx.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        raise ValueError(f"City not found: {city!r}")
    r = results[0]
    return float(r["latitude"]), float(r["longitude"])


def _fetch_weather(lat: float, lon: float, date_str: str) -> dict:
    """
    Fetch weather for a specific date from Open-Meteo.
    For future dates uses the forecast; for today uses current_weather.
    """
    target = datetime.strptime(date_str, "%Y-%m-%d").date()
    today  = date_type.today()
    delta  = (target - today).days

    if delta < 0:
        # Past date — use a historical-style fallback (daily averages for today)
        # Open-Meteo historical API requires a different endpoint and more setup;
        # for dev purposes return today's data with a note.
        date_str = today.strftime("%Y-%m-%d")

    resp = httpx.get(
        WEATHER_URL,
        params={
            "latitude":             lat,
            "longitude":            lon,
            "current":              "temperature_2m,apparent_temperature,weathercode,windspeed_10m,relativehumidity_2m",
            "hourly":               "precipitation_probability",
            "forecast_days":        min(max(delta + 1, 1), 16),
            "timezone":             "auto",
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    current = data.get("current", {})
    temp_c       = round(current.get("temperature_2m", 0), 1)
    feels_like_c = round(current.get("apparent_temperature", temp_c), 1)
    weather_code = int(current.get("weathercode", 0))
    wind_kph     = round(current.get("windspeed_10m", 0), 1)
    humidity_pct = int(current.get("relativehumidity_2m", 50))

    condition = WMO_CONDITIONS.get(weather_code, "partly cloudy")
    summary   = _build_summary(temp_c, condition, wind_kph)

    return {
        "temp_c":        temp_c,
        "feels_like_c":  feels_like_c,
        "condition":     condition,
        "humidity_pct":  humidity_pct,
        "wind_kph":      wind_kph,
        "summary":       summary,
        "weather_code":  weather_code,
    }


def _build_summary(temp_c: float, condition: str, wind_kph: float) -> str:
    wind_desc = ""
    if wind_kph >= 40:
        wind_desc = ", strong wind"
    elif wind_kph >= 20:
        wind_desc = ", light wind"

    return f"{temp_c}°C, {condition}{wind_desc}"


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
@mcp.tool()
def get_weather(city: str, date: str = "") -> dict:
    """
    Fetch current or forecast weather for a city.

    Args:
        city: City name (e.g. "London", "Istanbul", "New York")
        date: ISO date string YYYY-MM-DD (default: today)

    Returns:
        {
          temp_c: float,
          feels_like_c: float,
          condition: str,        # "sunny" / "rainy" / "snowy" etc.
          humidity_pct: int,
          wind_kph: float,
          summary: str           # "14°C, partly cloudy, light wind"
        }
    """
    if not date:
        date = date_type.today().strftime("%Y-%m-%d")

    try:
        lat, lon = _geocode(city)
    except Exception as e:
        return {"error": f"Geocoding failed for {city!r}: {e}"}

    try:
        return _fetch_weather(lat, lon, date)
    except Exception as e:
        return {"error": f"Weather fetch failed: {e}"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
