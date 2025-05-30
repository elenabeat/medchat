import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime

import toml

# from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
import requests

from pydanticModels import ChatQuery, ChatResponse, ChatCompletion
from utils import get_model_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%d-%m-%Y_%H')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

# CONFIG = toml.load("config.toml")


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
    yield
    # Shutdown events
    pass


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
# Endpoint
#####################


@app.post("/chat_completion")
def chat_completion(request: ChatQuery) -> ChatCompletion:

    # Get model config
    get_model_config()

    # Get query embedding
    resp = requests.post(
        url="http://medchat-model:9090/embed_text/",
        json={"input_type": "query", "content": request.query},
    )
    if resp.status_code == 200:
        logger.info(f"Embedding generated successfully")

    # Generate response
    prompt = f"You are an expert medical assisstant. Briefly answer the user's question to the best of your ability.\nQUERY: {request.query}"
    resp = requests.post(
        url="http://medchat-model:9090/generate_text/",
        json={
            "messages": [
                {"role": "user", "content": prompt},
            ]
        },
    )
    logger.info(f"Response generated successfully")

    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f"An error occurred connecting to the model server: {resp}")


@app.post("/chat_response")
def chat_response(chat_query: ChatQuery) -> ChatResponse:
    """
    Generate a response to a chat query.

    Args:
        chat_query (ChatQuery): the query to respond to

    Returns:
        str: the response to the query
    """
    search_query = GENERATOR.generate_search_query(
        query=chat_query.query, chat_history=chat_query.chat_history
    )
    logger.info(f"Search Query: {search_query}")

    context = COLLECTION.query(
        query_texts=[search_query],
        n_results=CONFIG["TOP_K"],
    )
    logger.info(f"Context: {context}")
    context_str = "\n\n".join(context["documents"][0])

    response = GENERATOR.generate_chat_response(
        query=chat_query.query,
        chat_history=chat_query.chat_history,
        context=context_str,
    )

    return ChatResponse(
        response=response,
        context={
            "documents": context["documents"][0],
            "metadata": context["metadatas"][0],
        },
    )
