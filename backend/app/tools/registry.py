from app.tools.calculator import calculator
from app.tools.weather import get_weather
from app.tools.live_search import live_search
from app.tools.datetime import get_datetime


AVAILABLE_TOOLS = [
    calculator,
    get_weather,
    live_search,
    get_datetime,
]