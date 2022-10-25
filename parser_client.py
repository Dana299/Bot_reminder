import random
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

URL = 'https://www.anekdot.ru/last/good/'

# print(anecdots)

class Parser:
    def __init__(self) -> None:
        pass

    def setup(self) -> None:
        pass

    @staticmethod
    def parse_url(*args, **kwargs) -> list[str]:
        today = date.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%d')
        url = f'https://www.anekdot.ru/release/anekdot/day/{today}/'
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')
        anecdots = [c.text for c in soup.find_all('div', class_='text')]
        return anecdots

if __name__ == '__main__':
    jokes_parser = Parser()
    print(jokes_parser.parse_url())