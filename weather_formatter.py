import datetime

from weather_api_service import Weather, WeatherType


def format_weather(weather: Weather) -> str:
    """"Formats Weather data and returns string"""
    return (f"Текущее время и дата: "
            f"{datetime.datetime.now().strftime('%d/%m/%Y, %H:%M')}\n"
            f"Сейчас за окном {round(weather.temperature)}°С, "
            f"{weather.weather_type.value}\n"
            f"Влажность воздуха: {weather.humidity}%\n"
            f"Ощущается как {round(weather.feels_like)}°С\n"
            f"Восход в {weather.sunrise.strftime('%H:%M')}\n"
            f"Закат в {weather.sunset.strftime('%H:%M')}"
            )


if __name__ == "__main__":
    print(format_weather(Weather(temperature=7.2,
                                 feels_like=7,
                                 weather_type=WeatherType.CLOUDS,
                                 humidity=64,
                                 sunrise=datetime.datetime(2022, 10, 21, 7, 52, 1),
                                 sunset=datetime.datetime(2022, 10, 21, 17, 34, 53),
                                 city='Saint-Petersburg, Russia')))

