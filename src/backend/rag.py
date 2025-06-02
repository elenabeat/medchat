import logging
from datetime import datetime

from sqlalchemy import Engine

from languageModels import (
    generate_chat_response,
    generate_search_query,
    embed_texts,
    rerank_chunks,
)
from ormModels import Message, MessageContext
from pydanticModels import ChatQuery, ChatResponse
from sqlFunctions import vector_search, insert_data

logger = logging.getLogger(__name__)


def rag(request: ChatQuery, engine: Engine) -> ChatResponse:

    received_at = datetime.now()

    # Generate Search Query
    search_query = generate_search_query(
        query=request.query, chat_history=request.chat_history
    )
    # Remove "QUESTION:" from the start of the search query, if present
    if search_query.upper().strip().startswith("QUESTION:"):
        search_query = search_query[len("QUESTION:") :].strip()
    logger.info(f"Search Query: {search_query}")

    # Embed Search Query
    embeddings = embed_texts(input_type="query", texts=search_query)

    # Retrieve Context
    context = vector_search(vector=embeddings[0], engine=engine)

    # Rerank with Cross-Encoder
    rerank_results = rerank_chunks(
        query=search_query,
        chunks=[chunk.text for chunk in context],
    )

    # Keep only the top chunks
    top_indices = [
        i for i in rerank_results.topk(3).indices if rerank_results[i] >= 5.0
    ]
    context = [context[i] for i in top_indices]
    scores = [rerank_results[i].item() for i in top_indices]
    context_retreived_at = datetime.now()
    logger.info(f"Context Scores: {scores}")

    # Generate Chat Response
    context_str = "\n\n".join([f"{chunk.text}" for chunk in context])

    response = generate_chat_response(
        query=search_query,
        context=context_str,
    )

    respone_at = datetime.now()

    logger.info(f"Response: {response}")
    logger.info(f"Response Time: {respone_at - received_at}")

    # Log message in the database
    message_data = {
        "session_id": request.session_id,
        "query": request.query,
        "received_at": received_at,
        "search_query": search_query,
        "context_retreived_at": context_retreived_at,
        "response_at": respone_at,
        "response": response,
        "is_good": None,
    }
    message = insert_data(
        engine=engine,
        table=Message,
        data=message_data,
    )[0]

    # If context found log it with this message in the database
    context_data = [
        {
            "chunk_id": chunk.chunk_id,
            "message_id": message.message_id,
        }
        for chunk in context
    ]
    if context_data:
        insert_data(
            engine=engine,
            table=MessageContext,
            data=context_data,
        )

    return ChatResponse(
        response=response,
        message_id=message.message_id,
        context=[
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "score": score,
                "title": chunk.article.title if chunk.article else None,
                "authors": chunk.article.authors if chunk.article else None,
                "start_page": chunk.article.start_page if chunk.article else None,
                "end_page": chunk.article.end_page if chunk.article else None,
                "filename": (
                    chunk.article.file.filename
                    if chunk.article and chunk.article.file
                    else None
                ),
            }
            for chunk, score in zip(context, scores)
        ],
    )
