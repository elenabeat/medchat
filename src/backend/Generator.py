import logging

import requests

from pydanticModels import ChatCompletion

logger = logging.getLogger(__name__)


class Generator:

    def __init__(self, model_server: str):
        self.model_server = model_server

    def chat_completion(self, request: ChatCompletion) -> ChatCompletion:
        resp = requests.post(
            url=f"{self.model_server}/generate_text/",
            json={"messages": [message.__dict__ for message in request.messages]},
        )
        logger.info(f"Response generated successfully")

        if resp.status_code == 200:
            return ChatCompletion(**resp.json())
