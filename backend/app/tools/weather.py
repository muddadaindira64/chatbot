import requests
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """
    Get current weather of any city.
    Use this tool for weather, temperature, rain and forecast questions.
    """


    # 1. Get coordinates

    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city}"
        "&count=1"
    )


    geo_response = requests.get(
        geo_url
    ).json()


    if "results" not in geo_response:
        return f"Cannot find location {city}"


    location = geo_response["results"][0]


    lat = location["latitude"]
    lon = location["longitude"]



    # 2. Get weather


    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&current_weather=true"
    )


    weather_response = requests.get(
        weather_url
    ).json()


    current = weather_response["current_weather"]



    return f"""
Current weather in {city}

Temperature:
{current['temperature']} °C

Wind Speed:
{current['windspeed']} km/h

Weather Code:
{current['weathercode']}
"""