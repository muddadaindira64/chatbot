from datetime import date, timedelta
import requests

from langchain_core.tools import tool


@tool
def get_weather(city: str, date: str = "") -> str:
    """
    Get weather information for a city.

    Supports:
    - current weather
    - today
    - tomorrow
    - yesterday
    - specific date

    Date can be:
    - today
    - tomorrow
    - yesterday
    - YYYY-MM-DD

    If date is empty, current weather is returned.
    """

    print(
        f"WEATHER TOOL INPUT -> city={city}, date={date}"
    )
    # --------------------------------------------------
    # 1. Get city coordinates
    # --------------------------------------------------

    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=10,
    ).json()

    if "results" not in geo_response:
        return f"Cannot find location: {city}"

    location = geo_response["results"][0]

    lat = location["latitude"]
    lon = location["longitude"]

    # --------------------------------------------------
    # 2. Current weather
    # --------------------------------------------------

    if not date:

        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,"
                    "apparent_temperature,"
                    "relative_humidity_2m,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto",
            },
            timeout=10,
        ).json()

        current = weather_response["current"]

        return f"""
Current weather in {city}:

Temperature: {current["temperature_2m"]} °C
Feels like: {current["apparent_temperature"]} °C
Humidity: {current["relative_humidity_2m"]}%
Precipitation: {current["precipitation"]} mm
Wind Speed: {current["wind_speed_10m"]} km/h
Weather Code: {current["weather_code"]}
""".strip()

    # --------------------------------------------------
    # 3. Resolve relative dates
    # --------------------------------------------------

    today = __import__("datetime").date.today()

    requested_date = date.lower().strip()

    if requested_date == "today":
        target_date = today

    elif requested_date == "tomorrow":
        target_date = today + timedelta(days=1)

    elif requested_date == "yesterday":
        target_date = today - timedelta(days=1)

    else:
        try:
            target_date = __import__("datetime").datetime.strptime(
                date,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return (
                "Invalid date. Use today, tomorrow, yesterday, "
                "or YYYY-MM-DD."
            )

    target_date_str = target_date.isoformat()

    # --------------------------------------------------
    # 4. Historical / forecast API
    # --------------------------------------------------

    if target_date < today:

        url = "https://archive-api.open-meteo.com/v1/archive"

    else:

        url = "https://api.open-meteo.com/v1/forecast"

    # --------------------------------------------------
    # 5. Get daily weather
    # --------------------------------------------------

    weather_response = requests.get(
        url,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": target_date_str,
            "end_date": target_date_str,
            "daily": (
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_sum,"
                "precipitation_probability_max,"
                "weather_code"
            ),
            "timezone": "auto",
        },
        timeout=10,
    ).json()

    if "daily" not in weather_response:
        return (
            f"No weather data available for "
            f"{city} on {target_date_str}."
        )

    daily = weather_response["daily"]

    # --------------------------------------------------
    # 6. Extract data
    # --------------------------------------------------

    max_temp = daily["temperature_2m_max"][0]
    min_temp = daily["temperature_2m_min"][0]
    precipitation = daily["precipitation_sum"][0]
    weather_code = daily["weather_code"][0]

    rain_probability = daily.get(
        "precipitation_probability_max"
    )

    if rain_probability:
        rain_probability = rain_probability[0]
    else:
        rain_probability = None

    # --------------------------------------------------
    # 7. Final result
    # --------------------------------------------------

    rain_text = (
        f"{rain_probability}%"
        if rain_probability is not None
        else "Not available"
    )

    return f"""
Weather in {city} on {target_date_str}:

Maximum Temperature: {max_temp} °C
Minimum Temperature: {min_temp} °C
Rain Probability: {rain_text}
Precipitation: {precipitation} mm
Weather Code: {weather_code}
""".strip()