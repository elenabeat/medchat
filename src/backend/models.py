import logging
import json
from typing import List, Literal

from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModel,
)
import torch
import toml

logger = logging.getLogger(__name__)
CONFIG = toml.load("config.toml")
PROMPTS = json.load(open("prompts.json"))

# Load inference model
inference_tokenizer = AutoTokenizer.from_pretrained(CONFIG["INFERENCE_MODEL"])
inference_model = AutoModelForCausalLM.from_pretrained(
    CONFIG["INFERENCE_MODEL"],
    device_map=CONFIG["DEVICE_MAP"],
    attn_implementation="flash_attention_2",
)
INFERENCE_PIPELINE = pipeline(
    task="text-generation",
    model=inference_model,
    tokenizer=inference_tokenizer,
    do_sample=CONFIG["DO_SAMPLE"],
    max_new_tokens=CONFIG["MAX_NEW_TOKENS"],
)
logger.info("Inference model loaded successfully.")

# Load query embedding model
QUERY_EMBEDDING_TOKENIZER = AutoTokenizer.from_pretrained(
    CONFIG["QUERY_EMBEDDING_MODEL"]
)
QUERY_EMBEDDING_MODEL = AutoModel.from_pretrained(
    CONFIG["QUERY_EMBEDDING_MODEL"], device_map=CONFIG["DEVICE_MAP"]
)

# Load article embedding model
ARTICLE_EMBEDDING_TOKENIZER = AutoTokenizer.from_pretrained(
    CONFIG["ARTICLE_EMBEDDING_MODEL"]
)
ARTICLE_EMBEDDING_MODEL = AutoModel.from_pretrained(
    CONFIG["ARTICLE_EMBEDDING_MODEL"], device_map=CONFIG["DEVICE_MAP"]
)

# Load cross-encoder model
CROSS_ENCODER_TOKENIZER = AutoTokenizer.from_pretrained(CONFIG["CROSS_ENCODER_MODEL"])
CROSS_ENCODER_MODEL = AutoModel.from_pretrained(
    CONFIG["CROSS_ENCODER_MODEL"], device_map=CONFIG["DEVICE_MAP"]
)

logger.info("Embedding and cross-encoder models loaded successfully.")


def embed_texts(
    input_type: Literal["article", "query"], texts: List[str]
) -> torch.tensor:
    """
    Generate embeddings for the input texts.

    Args:
        input_type (Literal['article', 'query']): Type of input, either 'query' or 'article'.
            Determines which model and tokenizer to use for embedding.
        texts (List[str]): List of input texts to embed.

    Returns:
        torch.tensor: Embeddings for the input texts with shape (input_length, embedding_dim).
    """
    if input_type == "query":
        tokenizer = QUERY_EMBEDDING_TOKENIZER
        model = QUERY_EMBEDDING_MODEL
    elif input_type == "article":
        tokenizer = ARTICLE_EMBEDDING_TOKENIZER
        model = ARTICLE_EMBEDDING_MODEL
    else:
        raise ValueError("Invalid input type. Must be 'query' or 'article'.")

    inputs = tokenizer(
        texts,
        padding=True,
        truncation=True,
        return_tensors="pt",
        max_length=512,
    ).to("cuda")

    with torch.no_grad():
        outputs = model(**inputs)

    # Use the last hidden state as the embedding
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings.cpu()


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


def generate_search_query(query: str, chat_history: str) -> str:

    sys_prompt = PROMPTS["system_prompt"]
    search_prompt = PROMPTS["search_prompt"].format(
        chat_history=chat_history, question=query
    )

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": search_prompt},
    ]

    outputs = INFERENCE_PIPELINE(messages)

    return outputs[0]["generated_text"]


def generate_chat_response(query: str, chat_history: str, context: str) -> str:

    sys_prompt = PROMPTS["system_prompt"]
    chat_prompt = PROMPTS["chat_prompt"].format(
        chat_history=chat_history, question=query, context=context
    )

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": chat_prompt},
    ]

    outputs = INFERENCE_PIPELINE(messages)

    return outputs[0]["generated_text"]
