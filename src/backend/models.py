import logging
from datetime import datetime
from typing import List

from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModel,
)
import torch
import toml

from pydanticModels import ChatCompletion, Message, EmbeddingRequest

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%d-%m-%Y_%H')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

CONFIG = toml.load("config.toml")

# Load inference model
tokenizer = AutoTokenizer.from_pretrained(CONFIG["INFERENCE_MODEL"])
model = AutoModelForCausalLM.from_pretrained(
    CONFIG["INFERENCE_MODEL"],
    device_map=CONFIG["DEVICE_MAP"],
    attn_implementation="flash_attention_2",
)
INFERENCE_PIPELINE = pipeline(
    task="text-generation",
    model=model,
    tokenizer=tokenizer,
    do_sample=CONFIG["DO_SAMPLE"],
    max_new_tokens=CONFIG["MAX_NEW_TOKENS"],
)
logger.info("Inference model loaded successfully.")

# Load query embedding model
QUERY_EMBEDDING_TOKENIZER = AutoTokenizer.from_pretrained(CONFIG["EMBEDDING_MODEL"])
QUERY_EMBEDDING_MODEL = AutoModel.from_pretrained(CONFIG["EMBEDDING_MODEL"])


# Load article embedding model
ARTICLE_EMBEDDING_TOKENIZER = AutoTokenizer.from_pretrained(
    CONFIG["ARTICLE_EMBEDDING_MODEL"]
)
ARTICLE_EMBEDDING_MODEL = AutoModel.from_pretrained(CONFIG["ARTICLE_EMBEDDING_MODEL"])

# Load cross-encoder model
CROSS_ENCODER_TOKENIZER = AutoTokenizer.from_pretrained(CONFIG["CROSS_ENCODER_MODEL"])
CROSS_ENCODER_MODEL = AutoModel.from_pretrained(CONFIG["CROSS_ENCODER_MODEL"])


def chat_completion(messages: List[Message]) -> ChatCompletion:
    """
    Generate text to compelte chat.

    Args:
        messages (List[Message]): List of previous messages.

    Returns:
        ChatCompletion: chat updated with the model's response.
    """

    outputs = INFERENCE_PIPELINE(text_inputs=[message.__dict__ for message in messages])

    return ChatCompletion(messages=outputs[0]["generated_text"])


def embed_texts(request: EmbeddingRequest) -> torch.tensor:
    """
    Generate embeddings for the input texts.

    Args:
        request (EmbeddingRequest): Request containing input type and content.

    Returns:
        torch,tensor: Embeddings for the input texts with shape (input_length, embedding_dim).
    """
    if request.input_type == "query":
        tokenizer = QUERY_EMBEDDING_TOKENIZER
        model = QUERY_EMBEDDING_MODEL
    elif request.input_type == "article":
        tokenizer = ARTICLE_EMBEDDING_TOKENIZER
        model = ARTICLE_EMBEDDING_MODEL
    else:
        raise ValueError("Invalid input type. Must be 'query' or 'article'.")

    inputs = tokenizer(
        request.texts if isinstance(request.texts, list) else [request.texts],
        padding=True,
        truncation=True,
        return_tensors="pt",
        max_length=512,
    ).to("cuda")

    with torch.no_grad():
        outputs = model(**inputs)

    # Use the last hidden state as the embedding
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings


def rerank(query: str, chunks: List[str]) -> torch.tensor:
    """
    Rerank chunks based on the query using a cross-encoder model.

    Args:
        query (str): The query string.
        chunks (List[str]): List of chunk strings to be ranked.

    Returns:
        torch.tensor: Scores for each chunk based on relevance the query.
            Higher scores indicate more relevant chunks.
    """

    encoded = CROSS_ENCODER_TOKENIZER(
        [[query, chunk] for chunk in chunks],
        truncation=True,
        padding=True,
        return_tensors="pt",
        max_length=512,
    ).to("cuda")

    logits = CROSS_ENCODER_MODEL(**encoded).logits.squeeze(dim=1)

    return logits
