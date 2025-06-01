from typing import Dict, List, Any, Literal

from pydantic.dataclasses import dataclass


@dataclass
class SessionRequest:
    """
    Dataclass for a session request.
    Attributes:
        user_id (int): the ID of the user requesting the session
    """

    user_id: int


@dataclass
class SessionResponse:
    """
    Dataclass for a session response.
    Attributes:
        session_id (int): the ID of the created session
        user_id (int): the ID of the user associated with the session
    """

    session_id: int
    user_id: int


@dataclass
class ChatQuery:
    """
    Dataclass for a chat query.

    Attributes:
        query (str): the query to respond to
        chat_history (str): the chat history
        session_id (int): the session ID for the chat
    """

    query: str
    chat_history: str
    session_id: int


@dataclass
class ChatResponse:
    """
    Dataclass for a chat response.

    Attributes:
        response (str): the response to the query
        context (Dict[str, List[Any]]): the context used to generate the response,
            containing documents and metadata
    """

    response: str
    context: List[
        Dict[str, Any]
    ]  # List of dictionaries containing context documents and metadata


@dataclass
class Message:
    """
    Dataclass for a chat message.

    Attributes:
        role (Literal["user", "system", "assistant", "generated_text"]): the role of the message
        content (str): the content of the message
    """

    role: Literal["user", "system", "assistant", "generated_text"]
    content: str


@dataclass
class ChatCompletion:
    """
    Dataclass for a chat completion request.

    Attributes:
        messages (List[Message]): a list of messages in the chat
    """

    messages: List[Message]
