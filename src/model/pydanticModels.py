from typing import Dict, List, Any, Literal

from pydantic.dataclasses import dataclass


@dataclass
class Message:
    """
    Dataclass for a chat message.
    """

    role: Literal["user", "system", "assistant", "generated_text"]
    content: str


@dataclass
class ChatCompletion:
    messages: List[Message]


@dataclass
class EmbeddingRequest:
    input_type: Literal["query", "article"]
    content: str | List[str]


@dataclass
class ModelDetails:
    inference_model: str
    embedding_model: str
    device_map: str
    max_new_tokens: int
    do_sample: bool
