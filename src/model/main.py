import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModel,
)
import toml

from pydanticModels import ChatCompletion, EmbeddingRequest, ModelDetails

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%d-%m-%Y_%H')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

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

    # Load inference model
    tokenizer = AutoTokenizer.from_pretrained(CONFIG["INFERENCE_MODEL"])
    model = AutoModelForCausalLM.from_pretrained(
        CONFIG["INFERENCE_MODEL"],
        device_map=CONFIG["DEVICE_MAP"],
        attn_implementation="flash_attention_2",
    )

    global INFERENCE_PIPELINE
    INFERENCE_PIPELINE = pipeline(
        task="text-generation",
        model=model,
        tokenizer=tokenizer,
        do_sample=CONFIG["DO_SAMPLE"],
        max_new_tokens=CONFIG["MAX_NEW_TOKENS"],
    )

    # Load embedding model
    global EMBEDDING_TOKENIZER, EMBEDDING_MODEL
    EMBEDDING_TOKENIZER = AutoTokenizer.from_pretrained(CONFIG["EMBEDDING_MODEL"])
    EMBEDDING_MODEL = AutoModel.from_pretrained(CONFIG["EMBEDDING_MODEL"])

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

    Returns:import requests
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


@app.get("/model_details/")
def model_details() -> ModelDetails:
    """
    Get details on the currently running models.

    Returns:
        ModelDetails: details about the current model configuration.
    """

    return ModelDetails(
        inference_model=CONFIG["INFERENCE_MODEL"],
        embedding_model=CONFIG["EMBEDDING_MODEL"],
        device_map=CONFIG["DEVICE_MAP"],
        max_new_tokens=CONFIG["MAX_NEW_TOKENS"],
        do_sample=CONFIG["DO_SAMPLE"],
    )


@app.post("/generate_text/")
async def generate_text(request: ChatCompletion) -> ChatCompletion:
    """
    Generate text to compelte chat.

    Args:
        request (ChatCompletion): previous chat messages.

    Returns:
        ChatCompletion: chat updated with the model's response.
    """

    outputs = INFERENCE_PIPELINE(
        text_inputs=[message.__dict__ for message in request.messages]
    )

    return ChatCompletion(messages=outputs[0]["generated_text"])


@app.post("/embed_text/")
async def embed_text(request: EmbeddingRequest) -> List[List[float]]:

    encoded = EMBEDDING_TOKENIZER(
        request.content,
        truncation=True,
        padding=True,
        return_tensors="pt",
        # max_length=64,
    )
    outputs = EMBEDDING_MODEL(**encoded).last_hidden_state[:, 0, :]

    logger.info(f"Outputs: {outputs}")

    return outputs
