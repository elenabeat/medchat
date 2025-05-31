import logging
from datetime import datetime

from sqlalchemy import Engine

from models import generate_chat_response, generate_search_query, embed_texts
from pydanticModels import ChatQuery, ChatResponse
from sqlFunctions import vector_search

logger = logging.getLogger(__name__)


def rag(request: ChatQuery, engine: Engine) -> ChatResponse:

    received_at = datetime.now()

    chat_history_str = "\n".join(
        [f"{msg.role}: {msg.content}" for msg in request.chat_history]
    )

    # Generate Search Query
    search_query = generate_search_query(
        query=request.query, chat_history=request.chat_history
    )
    logger.info(f"Search Query: {search_query}")

    # Embed Search Query
    embedding = embed_texts(input_type="query", texts=search_query)

    # Retrieve Context
    context = vector_search(vector=embedding, engine=engine)

    logger.info(f"Context: {context}")
