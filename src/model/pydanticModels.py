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
