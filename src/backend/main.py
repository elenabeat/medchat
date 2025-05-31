import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime

import toml
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%d-%m-%Y_%H')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

from pydanticModels import ChatQuery, ChatResponse
from sqlFunctions import create_connection
from textProcessing import process_directory


CONFIG = toml.load("config.toml")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Controls startup and shutdown events for the FastAPI application.
    Anything before the yield statement is executed on startup,
    and anything after is executed on shutdown.

    Args:
        app (FastAPI): unaccessed here but necessary for FASTAPI to accept this
            lifespan.
    """
    # Startup events

    # Create engine
    global ENGINE
    ENGINE = create_connection()

    # Process sources directory
    process_directory(
        directory=Path(CONFIG["SOURCES_DIR"]),
        engine=ENGINE,
    )

    yield
    # Shutdown events


app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def custom_form_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Sends formats detailed responses for any requests that trigger validation errors.

    Args:
        request (Request): request triggering the validation error.
        exc (RequestValidationError): the validation error exception that was raised.

    Returns:
        JSONResponse: json response explaining what fields were missing, of the wrong
            type, etc.
    """

    reformatted_message = defaultdict(list)
    for pydantic_error in exc.errors():
        loc, msg = pydantic_error["loc"], pydantic_error["msg"]
        filtered_loc = loc[1:] if loc[0] in ("body", "query", "path") else loc
        field_string = ".".join(filtered_loc)  # nested fields with dot-notation
        reformatted_message[field_string].append(msg)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {"detail": "Invalid request", "errors": reformatted_message}
        ),
    )


#####################
# Endpoints
#####################


# @app.post("/chat_response")
# def chat_response(chat_query: ChatQuery) -> ChatResponse:
#     """
#     Generate a response to a chat query.

#     Args:
#         chat_query (ChatQuery): the query to respond to

#     Returns:
#         str: the response to the query
#     """
#     search_query = GENERATOR.generate_search_query(
#         query=chat_query.query, chat_history=chat_query.chat_history
#     )
#     logger.info(f"Search Query: {search_query}")

#     context = COLLECTION.query(
#         query_texts=[search_query],
#         n_results=CONFIG["TOP_K"],
#     )
#     logger.info(f"Context: {context}")
#     context_str = "\n\n".join(context["documents"][0])

#     response = GENERATOR.generate_chat_response(
#         query=chat_query.query,
#         chat_history=chat_query.chat_history,
#         context=context_str,
#     )

#     return ChatResponse(
#         response=response,
#         context={
#             "documents": context["documents"][0],
#             "metadata": context["metadatas"][0],
#         },
#     )
