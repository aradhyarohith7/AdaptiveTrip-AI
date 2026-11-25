
import json
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
MAX_FORECAST_DAYS = 16

HEADERS = {
    "User-Agent": "AdaptiveTripAI/1.0 (educational travel planning project)",
    "Accept": "application/json"
}


def get_weather_description(weather_code):
    """Convert a weather code into a simple description."""

    weather_conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }

    return weather_conditions.get(weather_code, "Unknown condition")


def get_weather(
    latitude,
    longitude,
    forecast_days=7,
    start_date=None,
    end_date=None
):
    """Get weather for a forecast period or specific trip dates."""

    latitude = float(latitude)
    longitude = float(longitude)

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max,"
            "precipitation_sum"
        ),
        "timezone": "auto"
    }

    missing_dates = []

    if start_date is not None or end_date is not None:

        if start_date is None or end_date is None:
            raise ValueError("Both start_date and end_date are required.")

        trip_start = date.fromisoformat(str(start_date))
        trip_end = date.fromisoformat(str(end_date))

        if trip_end < trip_start:
            raise ValueError("End date cannot be before start date.")

        today = date.today()
        last_forecast_date = today + timedelta(
            days=MAX_FORECAST_DAYS - 1
        )

        available_start = max(trip_start, today)
        available_end = min(trip_end, last_forecast_date)

        total_trip_days = (trip_end - trip_start).days + 1

        if available_start > available_end:

            return {
                "available": False,
                "full_coverage": False,
                "latitude": latitude,
                "longitude": longitude,
                "source": "Open-Meteo",
                "timezone": None,
                "forecast": [],
                "coverage_start": None,
                "coverage_end": None,
                "missing_dates": [
                    (trip_start + timedelta(days=i)).isoformat()
                    for i in range(total_trip_days)
                ],
                "message": (
                    "Weather forecast is unavailable for the requested "
                    "trip dates. They are outside the current forecast window."
                )
            }

        params["start_date"] = available_start.isoformat()
        params["end_date"] = available_end.isoformat()

        available_days = (available_end - available_start).days + 1

        for i in range(total_trip_days):
            requested_date = trip_start + timedelta(days=i)

            if not available_start <= requested_date <= available_end:
                missing_dates.append(requested_date.isoformat())

    else:

        if (
            not isinstance(forecast_days, int)
            or not 1 <= forecast_days <= MAX_FORECAST_DAYS
        ):
            raise ValueError("Forecast days must be between 1 and 16.")

        params["forecast_days"] = forecast_days

    url = f"{OPEN_METEO_URL}?{urlencode(params)}"
    request = Request(url, headers=HEADERS)

    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        daily_data = data.get("daily")

        if not daily_data or not daily_data.get("time"):
            raise ValueError("Weather service returned no forecast data.")

        forecast = []

        for index, weather_date in enumerate(daily_data["time"]):

            weather_code = daily_data["weather_code"][index]

            forecast.append({
                "date": weather_date,
                "condition": get_weather_description(weather_code),
                "weather_code": weather_code,
                "temperature_max": daily_data[
                    "temperature_2m_max"
                ][index],
                "temperature_min": daily_data[
                    "temperature_2m_min"
                ][index],
                "rain_probability": daily_data[
                    "precipitation_probability_max"
                ][index],
                "precipitation_mm": daily_data[
                    "precipitation_sum"
                ][index]
            })

        return {
            "available": True,
            "full_coverage": len(missing_dates) == 0,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": data.get("timezone"),
            "source": "Open-Meteo",
            "coverage_start": forecast[0]["date"],
            "coverage_end": forecast[-1]["date"],
            "missing_dates": missing_dates,
            "forecast": forecast
        }

    except HTTPError as error:
        raise RuntimeError(
            f"Weather service returned HTTP {error.code}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Could not connect to weather service: {error.reason}"
        ) from error

    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(
            "Weather service returned an unexpected response."
        ) from error


if __name__ == "__main__":

    try:
        from services.route_service import geocode_place

        location = geocode_place("Baga Beach, Goa, India")

        test_start = date.today()
        test_end = test_start + timedelta(days=6)

        result = get_weather(
            location["latitude"],
            location["longitude"],
            start_date=test_start.isoformat(),
            end_date=test_end.isoformat()
        )

        print("\n========== ADAPTIVETRIP AI WEATHER TEST ==========")
        print("Location:", location["name"])
        print("Location Type:", location["type"])
        print("Weather Source:", result["source"])
        print("Timezone:", result["timezone"])
        print("Full Coverage:", result["full_coverage"])

        for day in result["forecast"]:

            print("\nDate:", day["date"])
            print("Condition:", day["condition"])
            print("Maximum Temperature:", day["temperature_max"], "°C")
            print("Minimum Temperature:", day["temperature_min"], "°C")
            print("Rain Probability:", day["rain_probability"], "%")
            print("Expected Precipitation:", day["precipitation_mm"], "mm")

        if result["missing_dates"]:
            print("\nWeather unavailable for:", result["missing_dates"])

        print("\n==================================================")

    except Exception as error:
        print("\nWeather test failed:", error)
