import logging
from datetime import datetime

from sqlalchemy import Engine

from models import generate_chat_response, generate_search_query, embed_texts
from pydanticModels import ChatQuery, ChatResponse
from sqlFunctions import vector_search

logger = logging.getLogger(__name__)


def rag(request: ChatQuery, engine: Engine) -> ChatResponse:

    received_at = datetime.now()

    # Generate Search Query
    search_query = generate_search_query(
        query=request.query, chat_history=request.chat_history
    )
    logger.info(f"Search Query: {search_query}")

    # Embed Search Query
    embeddings = embed_texts(input_type="query", texts=search_query)
    logger.info(f"Embeddings: {embeddings}")

    # Retrieve Context
    context = vector_search(vector=embeddings[0], engine=engine)

    logger.info(f"Context: {context}")
