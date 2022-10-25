import json
import urllib.request
from datetime import date, datetime
from enum import Enum
from typing import Literal, NamedTuple
from urllib.error import URLError

from requests import JSONDecodeError

from coordinates import Coordinates
from exceptions import ApiServiceError, UnconfiguredVariable

Celsius = int


class WeatherType(Enum):
    THUNDERSTORM = "гроза"
    DRIZZLE = "изморозь"
    RAIN = "дождь"
    SNOW = "снег"
    CLEAR = "ясно"
    FOG = "туман"
    CLOUDS = "облачно"


# print(WeatherType.CLEAR) -> WeatherType.CLEAR
# print(WeatherType.CLEAR.value) -> Ясно
# print(WeatherType.CLEAR.name) -> CLEAR
# print(isinstance(WeatherType.CLEAR, WeatherType)) -> True


class Weather(NamedTuple):
    temperature: Celsius
    feels_like: Celsius
    weather_type: WeatherType
    humidity: int
    sunrise: datetime
    sunset: datetime
    city: str


def get_openweather_response(
    open_weather_url: str, open_weather_token: str, coordinates: Coordinates
) -> str:
    url = open_weather_url.format(*coordinates, OPEN_WEATHER_TOKEN=open_weather_token)
    try:
        return urllib.request.urlopen(url).read()
    except URLError:
        raise ApiServiceError


def get_weather(
    open_weather_url: str, open_weather_token: str, coordinates: Coordinates
) -> Weather:
    """Requests weather in OpenWeather API and returns it"""
    openweather_response = get_openweather_response(
        open_weather_url, open_weather_token, coordinates
    )
    weather = _parse_openweather_response(openweather_response)
    return weather


def _parse_openweather_response(openweather_response: str) -> Weather:
    try:
        openweather_dict = json.loads(openweather_response)
    except JSONDecodeError:
        raise ApiServiceError
    return Weather(
        temperature=openweather_dict["main"]["temp"],
        feels_like=openweather_dict["main"]["feels_like"],
        weather_type=parse_weather_type(openweather_dict),
        humidity=openweather_dict["main"]["humidity"],
        sunrise=parse_time(openweather_dict, "sunrise"),
        sunset=parse_time(openweather_dict, "sunset"),
        city="Saint-Petersburg, Russia",
    )


def parse_weather_type(openweather_dict: dict) -> WeatherType:
    try:
        weather_code = openweather_dict["weather"][0]["id"]
    except (IndexError, KeyError):
        raise ApiServiceError
    weather_types = {
        "2": WeatherType.THUNDERSTORM,
        "3": WeatherType.DRIZZLE,
        "5": WeatherType.RAIN,
        "6": WeatherType.SNOW,
        "7": WeatherType.FOG,
        "800": WeatherType.CLEAR,
        "80": WeatherType.CLOUDS,
    }
    for id, weather_type in weather_types.items():
        if str(weather_code).startswith(id):
            return weather_type
    raise ApiServiceError


def parse_time(
    openweather_dict: dict, time: Literal["sunrise"] | Literal["sunset"]
) -> datetime:
    return datetime.fromtimestamp(openweather_dict["sys"][time])
