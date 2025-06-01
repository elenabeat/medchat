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
from sqlalchemy import select
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.exc import NoResultFound

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%d-%m-%Y_%H')}.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

from ormModels import Session, Message
from pydanticModels import ChatQuery, ChatResponse, SessionRequest, FeedbackRequest
from rag import rag
from sqlFunctions import create_connection, insert_data
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


@app.post("/start_session")
def start_session(request: SessionRequest) -> int:

    session_data = {
        "user_id": request.user_id,
        "created_at": datetime.now(),
    }

    session = insert_data(
        engine=ENGINE,
        table=Session,
        data=session_data,
    )[0]
    logger.info(f"Session started: {session}")

    return session.session_id


@app.post("/chat_response")
def chat_response(request: ChatQuery) -> ChatResponse:
    """
    Generate a response to a chat query.

    Args:
        request (ChatQuery): the query to respond to

    Returns:
        ChatResponse: the model's response and any retrieved
            context.
    """

    resp = rag(request=request, engine=ENGINE)

    return resp


@app.post("/submit_feedback")
def submit_feedback(request: FeedbackRequest) -> JSONResponse:
    """
    Submit feedback for a chat response.

    Args:
        request (FeedbackRequest): the feedback to submit.
    """
    try:
        with SQLAlchemySession(ENGINE) as session:
            stmt = select(Message).where(Message.message_id == request.message_id)
            message = session.execute(stmt).scalars().one()
            message.is_good = request.is_good
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "Feedback submitted successfully."},
        )

    except NoResultFound as e:
        logger.warning(f"Message with id {request.message_id} not found: {e}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Message id not found."},
        )
