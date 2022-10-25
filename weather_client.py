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


class Weather(NamedTuple):
    temperature: Celsius
    feels_like: Celsius
    weather_type: WeatherType
    humidity: int
    sunrise: datetime
    sunset: datetime
    city: str


class StickerType(Enum):
    """Stickers id's"""
    BAD_REQUEST = "CAACAgEAAxkBAAEGLWRjVVt843h1pOGMjAjRfIZSUlposAACKAEAAv0KkAQjcThQM9MC1yoE"
    EXPECTATION = "CAACAgEAAxkBAAEGLWJjVVqZN1ZwVhlX3fM_0kXAbzDJXwACJgEAAv0KkASrHZqsq5972ioE"
    HELLO = "CAACAgEAAxkBAAEGLWZjVVuwpZMdqkAkATbDg5cFhIPufQACMgEAAv0KkASY50AccbMPRCoE"


class WeatherClient:

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def _get_openweather_response(
        self, open_weather_url: str, city: str) -> str:
        url = open_weather_url.format(city=city, OPEN_WEATHER_TOKEN=self.api_key)
        try:
            return urllib.request.urlopen(url).read()
        except URLError:
            raise ApiServiceError


    def get_weather(self, open_weather_url: str, city: str) -> Weather:
        """Requests weather in OpenWeather API and returns it"""
        openweather_response = self._get_openweather_response(
            open_weather_url, city
        )
        weather = self._parse_openweather_response(openweather_response)
        return weather


    def _parse_openweather_response(self, openweather_response: str) -> Weather:
        try:
            openweather_dict = json.loads(openweather_response)
        except JSONDecodeError:
            raise ApiServiceError
        return Weather(
            temperature=openweather_dict["main"]["temp"],
            feels_like=openweather_dict["main"]["feels_like"],
            weather_type=self._parse_weather_type(openweather_dict),
            humidity=openweather_dict["main"]["humidity"],
            sunrise=self._parse_time(openweather_dict, "sunrise"),
            sunset=self._parse_time(openweather_dict, "sunset"),
            city="Saint-Petersburg, Russia",
        )

    @staticmethod
    def _parse_weather_type(openweather_dict: dict) -> WeatherType:
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

    @staticmethod
    def _parse_time(
        openweather_dict: dict, time: Literal["sunrise"] | Literal["sunset"]
    ) -> datetime:
        return datetime.fromtimestamp(openweather_dict["sys"][time])

