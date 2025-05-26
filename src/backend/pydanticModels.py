from typing import Dict, List, Any, Literal

from pydantic.dataclasses import dataclass


@dataclass
class ChatQuery:
    """
    Dataclass for a chat query.

    Attributes:
        query (str): the query to respond to
        chat_history (str): the chat history
    """

    query: str
    chat_history: str


@dataclass
class ChatResponse:
    """
    Dataclass for a chat response.

    Attributes:
        response (str): the response to the query
    """

    response: str
    context: Dict[str, List[Any]]


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
    texts: str | List[str]
