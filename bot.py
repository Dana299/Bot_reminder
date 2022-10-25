import os
import random
import re
import sqlite3 as sq
from datetime import datetime
from time import sleep

import telebot
from dotenv import load_dotenv
from telebot.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    InlineKeyboardMarkup,
)

from db_handler import SQLiteClient, UserHandler
from exceptions import ApiServiceError, UnconfiguredVariable
from parser_client import Parser
from telegram_client import TelegramClient
from weather_client import StickerType, WeatherClient
from weather_formatter import format_weather

load_dotenv()  # take environment variables from .env.

try:
    TOKEN = os.environ["TOKEN"]
    OPEN_WEATHER_KEY = os.environ["OPEN_WEATHER_KEY"]
    OPEN_WEATHER_URL = os.environ["OPEN_WEATHER_URL"]
    ADMIN_CHAT_ID = os.environ["ADMIN_CHAT_ID"]
    OPEN_WEATHER_URL_CITY = os.environ["OPEN_WEATHER_URL_CITY"]
except KeyError as err:
    raise UnconfiguredVariable from err


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
user_id int PRIMARY KEY,
username text,
chat_id int,
city text,
registration_time DEFAULT CURRENT_TIMESTAMP
);
"""


if __name__ == "__main__":
    conn = sq.connect("users.db")
    # conn.execute("DROP TABLE IF EXISTS users")
    conn.execute(CREATE_TABLE)


class MyBot(telebot.TeleBot):
    def __init__(
        self,
        telegram_client: TelegramClient,
        user_handler: UserHandler,
        weather_client: WeatherClient,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.telegram_client = telegram_client
        self.user_handler = user_handler
        self.weather_client = weather_client

    def setup_resources(self):
        # готовит класс для работы
        self.user_handler.setup()


# разделение ответственности - один бот (клиент) для логирования ошибок,
# другой  - для выполнения задач
telegram_client = TelegramClient(token=TOKEN, base_url="https://api.telegram.org")
user_handler = UserHandler(SQLiteClient("users.db"))
weather_client = WeatherClient(api_key=OPEN_WEATHER_KEY)
bot = MyBot(
    token=TOKEN,
    telegram_client=telegram_client,
    user_handler=user_handler,
    weather_client=weather_client,
)
bot.setup_resources()


@bot.message_handler(commands=["start"])
def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id

    markup_constant = make_keyboardmarkup(
        "Получить данные о погоде 🌡☔", "Анекдот 😁", "Изменить название города 📍"
    )

    user = bot.user_handler.get_user(str(user_id))
    if user:
        bot.reply_to(
            message=message,
            text=str(f"Вы уже зарегестрированы. Ваш user id: {user_id}"),
            reply_markup=markup_constant,
        )
    else:
        bot.user_handler.create_user(
            user_id=str(user_id), username=str(username), chat_id=chat_id
        )
        markup = make_inlinemarkup("Ввести данные сейчас", "Продолжить позже")
        bot.send_sticker(chat_id=message.chat.id, sticker=StickerType.HELLO.value)
        bot.send_message(
            chat_id=message.chat.id,
            text=f"Привет, <b>{message.from_user.first_name}</b> ☺👋!\n"
            f"Я - {bot.get_me().first_name}. Я могу получать данные "
            "о погоде в твоем городе.\n"
            "Чтобы завершить регистрацию, необходимо указать свой "
            "город пребывания. Хотите сделать это "
            "прямо сейчас? Если нет, то вы можете дополнить свой "
            "профиль позднее, используя команду /edit_my_profile. ",
            reply_markup=markup,
            parse_mode="html",
        )
        bot.register_next_step_handler(message=message, callback=registration)


def registration(message: Message):
    if message.text in ("Нет", "Продолжить позже"):
        bot.send_message(
            chat_id=message.chat.id,
            text="Хорошо, ты можешь заполнить данные в любой момент по команде /edit_my_profile",
        )
    if message.text in ("Да", "Ввести данные сейчас"):
        bot.send_message(
            chat_id=message.chat.id,
            text="Приступим к редактированию профиля.\n"
            "Введите название города вашего пребывания на английском языке",
        )
        bot.register_next_step_handler(message, enter_city)


@bot.callback_query_handler(func=lambda call: True)
def callback(call: CallbackQuery):
    if call.message:
        if call.data == "neg":
            bot.send_message(
                chat_id=call.message.chat.id,
                text="Хорошо, ты можешь заполнить данные в любой момент по команде /edit_my_profile",
            )

        elif call.data == "pos":
            bot.send_message(
                chat_id=call.message.chat.id,
                text="Приступим к редактированию профиля.\n"
                "Введите название города вашего пребывания на английском языке.",
            )
            bot.register_next_step_handler(call.message, enter_city)


def enter_city(message: Message):
    if not re.fullmatch(r"[A-Z][a-zA-Z\s-]+", message.text):  # type: ignore
        bot.send_message(
            chat_id=message.chat.id,
            text="Введенное название некорректно. Название должно начинаться с "
            "заглавной буквы, может содержать только английские буквы, "
            "символ пробела и дефис.",
        )
        bot.register_next_step_handler(message, enter_city)
    else:
        bot.user_handler.update_value(str(message.chat.id), "city", str(message.text))
        bot.send_message(
            chat_id=message.chat.id,
            text="Спасибо! Ваши данные успешно внесены 😉\n"
            "Теперь вы можете узнать данные о погоде "
            "используя кнопки внизу экрана.",
        )


@bot.message_handler(commands=["edit_my_profile"])
def edit_profile(message: Message):
    markup_1 = make_inlinemarkup("Да", "Нет")
    markup_2 = make_inlinemarkup("Ввести данные сейчас", "Продолжить позже")
    current_city = bot.user_handler.get_value(
        value="city", user_id=str(message.from_user.id)
    )
    if current_city:
        bot.send_message(
            chat_id=message.from_user.id,
            text=f"Ваш текущий город: {current_city[0]}.\n"
            "Хотите изменить город вашего пребывания?\n",
            reply_markup=markup_1,
        )
    else:
        bot.send_message(
            chat_id=message.from_user.id,
            text="Вы пока не ввели город. Хотите сделать это сейчас?",
            reply_markup=markup_2,
        )
    bot.register_next_step_handler(message, registration)


@bot.message_handler(content_types=["text"])
def buttons_handler(message: Message):
    if message.text == "Получить данные о погоде 🌡☔":
        send_weather(message)
    elif message.text == "Изменить название города 📍":
        edit_profile(message)
    elif message.text == "Анекдот 😁":
        tell_joke(message)


def send_weather(message: Message):
    current_city = bot.user_handler.get_value(
        value="city", user_id=str(message.from_user.id)
    )
    if current_city:
        bot.send_sticker(chat_id=message.chat.id, sticker=StickerType.EXPECTATION.value)
        bot.send_message(chat_id=message.chat.id, text="Собираю данные, одну минуту...")
        try:
            current_weather = bot.weather_client.get_weather(
                OPEN_WEATHER_URL_CITY, city=current_city[0]
            )
            sleep(2)
            bot.send_message(
                chat_id=message.chat.id,
                text=f"Ваш текущий город: {current_city[0]}\n"
                f"{format_weather(current_weather)}",
            )
        except ApiServiceError:
            bot.send_sticker(
                chat_id=message.chat.id, sticker=StickerType.BAD_REQUEST.value
            )
            bot.send_message(
                chat_id=message.chat.id,
                text=f"Не получается отобразить погоду в городе {current_city[0]}.\n"
                "Введите корректное название города по команде /edit_my_profile",
            )

    else:
        bot.send_message(
            chat_id=message.chat.id,
            text="Вы не указали город текущего пребывания.\n"
            "Воспользуйтесь командой /edit_my_profile, чтобы ввести город.",
        )


def handle_say_something(message: Message):
    bot.reply_to(message, text="Спасибо за ответ! Хорошего дня :)")


@bot.message_handler(commands=["say_something"])
def say_something(message: Message):
    bot.reply_to(message=message, text="Гав-гав! 🐶")
    bot.register_next_step_handler(message, callback=handle_say_something)


@bot.message_handler(commands=["joke"])
def tell_joke(message: Message):
    bot.send_message(
        message.chat.id, text=random.choice(Parser().parse_url()), parse_mode="html"
    )


def make_keyboardmarkup(text_1: str, text_2: str, text_3: str) -> ReplyKeyboardMarkup:
    """Makes ReplyKeyboardMarkup with two buttons"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item_1 = KeyboardButton(text=text_1)
    item_2 = KeyboardButton(text=text_2)
    markup.row(item_1, item_2)
    item_3 = KeyboardButton(text=text_3)
    markup.add(item_3)
    return markup


def make_inlinemarkup(text_1: str, text_2: str) -> telebot.types.InlineKeyboardMarkup:
    """Makes InlineKeyboardMarkup with two answers - positive and negative"""
    markup = InlineKeyboardMarkup(row_width=2)
    item_1 = InlineKeyboardButton(text=text_1, callback_data="pos")
    item_2 = InlineKeyboardButton(text=text_2, callback_data="neg")
    markup.add(item_1, item_2)
    return markup


def create_error_message(error: Exception) -> str:
    data = datetime.strftime(datetime.now(), "%d/%m/%Y, %H:%M:%S")
    return f"{data} : {type(error).__name__}"


bot.polling(none_stop=True)
# while True:
#     try:
#         bot.polling()
#     except (json.JSONDecodeError, ConnectionError) as err:
#         print("Ошибка", err)
#         bot.telegram_client.post(
#             method="sendMessage",
#             params={"text": create_error_message(err), "chat_id": ADMIN_CHAT_ID},
#         )
#         requests.post(
#             f"https://api.telegram.org/bot5693373119:AAF19zHv4j5mCgpO53CKRIG4Lp_28kAYv40"
#             f"/sendMessage?chat_id=439019486&text="
#         )
#     except KeyboardInterrupt:
#         break
