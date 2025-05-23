import requests

from pydanticModels import ChatCompletion


class Generator:

    def __init__(self, model_server: str):
        self.model_server = model_server

    def chat_completion(self, messages: ChatCompletion):
        pass
