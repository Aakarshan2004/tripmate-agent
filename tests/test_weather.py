from app.tools.weather_tool import get_weather_forecast


weather = get_weather_forecast(
    destination="Goa",
    start_date="2026-10-01",
    end_date="2026-10-05"
)

for day in weather:
    print(day)