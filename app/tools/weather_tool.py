import os
import requests
from dotenv import load_dotenv
from app.models.schemas import WeatherDay

load_dotenv()

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")

GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/direct"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_weather_forecast(
    destination: str,
    start_date: str,
    end_date: str
) -> list[WeatherDay]:

    if not OPENWEATHER_KEY:
        raise RuntimeError("OPENWEATHER_KEY not set in .env")

    lat, lon = _geocode(destination)

    if lat is None:
        return []

    try:
        resp = requests.get(
            FORECAST_URL,
            params={
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_KEY,
                "units": "metric"
            },
            timeout=10
        )

        resp.raise_for_status()
        data = resp.json()

    except requests.RequestException as e:
        print(f"[weather_tool] Forecast request failed: {e}")
        return []

    return _aggregate_by_day(
        data.get("list", []),
        start_date,
        end_date
    )


def _geocode(
    destination: str
) -> tuple[float | None, float | None]:

    try:
        resp = requests.get(
            GEOCODE_URL,
            params={
                "q": destination,
                "limit": 1,
                "appid": OPENWEATHER_KEY
            },
            timeout=10
        )

        resp.raise_for_status()
        results = resp.json()

        if not results:
            print(
                f"[weather_tool] No geocode match for '{destination}'"
            )
            return None, None

        return results[0]["lat"], results[0]["lon"]

    except (requests.RequestException, KeyError, IndexError) as e:
        print(f"[weather_tool] Geocoding failed: {e}")
        return None, None


def _aggregate_by_day(
    entries: list[dict],
    start_date: str,
    end_date: str
) -> list[WeatherDay]:

    by_date: dict[str, list[dict]] = {}

    for entry in entries:

        date_str = entry.get("dt_txt", "").split(" ")[0]

        if not date_str:
            continue

        by_date.setdefault(date_str, []).append(entry)

    days = []

    for date_str, entries_for_day in by_date.items():
        if date_str < start_date or date_str > end_date:
            continue
        

        temps = [
            e["main"]["temp"]
            for e in entries_for_day
            if "main" in e
        ]

        conditions = [
            e["weather"][0]["description"]
            for e in entries_for_day
            if e.get("weather")
        ]

        rain = any(
            "rain" in e
            for e in entries_for_day
        )

        if not temps or not conditions:
            continue

        days.append(
            WeatherDay(
                date=date_str,
                condition=max(
                    set(conditions),
                    key=conditions.count
                ),
                temp_min=min(temps),
                temp_max=max(temps),
                rain_likely=rain
            )
        )

    return sorted(
        days,
        key=lambda d: d.date
    )