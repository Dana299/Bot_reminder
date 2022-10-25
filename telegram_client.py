import requests


class TelegramClient:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url

    def prepare_url(self, method: str):
        result_url = f"{self.base_url}/bot{self.token}/"
        if method is not None:
            result_url += method
        return result_url

    def post(
        self,
        method: str | None=None,
        params: dict | None=None,
        body: dict | None=None):
        url = self.prepare_url(method)
        resp = requests.post(url, params=params, data=body)
        return resp.json()

if __name__ == "__main__":
    pass
    # token = "5693373119:AAF19zHv4j5mCgpO53CKRIG4Lp_28kAYv40"
    # telegram_client = TelegramClient(token=token, base_url="https://api.telegram.org")
    # my_params = {"chat_id": 439019486, "text": "Error"}
    # print(telegram_client.post(method="sendMessage", params=my_params))

