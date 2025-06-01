import logging
import json
from typing import List, Literal

from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModel,
    AutoModelForSequenceClassification,
)
import torch
import toml

logger = logging.getLogger(__name__)
CONFIG = toml.load("config.toml")
PROMPTS = json.load(open("prompts.json"))

# Load inference model
INFERENCE_TOKENIZER = AutoTokenizer.from_pretrained(CONFIG["INFERENCE_MODEL"])
INFERENCE_MODEL = AutoModelForCausalLM.from_pretrained(
    CONFIG["INFERENCE_MODEL"],
    device_map=CONFIG["DEVICE_MAP"],
    attn_implementation="flash_attention_2",
)
# INFERENCE_PIPELINE = pipeline(
#     task="text-generation",
#     model=inference_model,
#     tokenizer=inference_tokenizer,
#     do_sample=CONFIG["DO_SAMPLE"],
#     temperature=CONFIG["TEMPERATURE"],
#     max_new_tokens=CONFIG["MAX_NEW_TOKENS"],
# )
logger.info("Inference model loaded successfully.")

# Load query embedding model
QUERY_EMBEDDING_TOKENIZER = AutoTokenizer.from_pretrained(
    CONFIG["QUERY_EMBEDDING_MODEL"]
)
QUERY_EMBEDDING_MODEL = AutoModel.from_pretrained(CONFIG["QUERY_EMBEDDING_MODEL"])

# Load cross-encoder model
CROSS_ENCODER_TOKENIZER = AutoTokenizer.from_pretrained(CONFIG["CROSS_ENCODER_MODEL"])
CROSS_ENCODER_MODEL = AutoModelForSequenceClassification.from_pretrained(
    CONFIG["CROSS_ENCODER_MODEL"]
)

logger.info("Embedding and cross-encoder models loaded successfully.")


def generate_text(
    prompt: str,
    enable_thinking: bool = True,
    max_new_tokens: int = CONFIG["MAX_NEW_TOKENS"],
) -> str:

    # Apply chat template to the prompt
    messages = [{"role": "user", "content": prompt}]
    text = INFERENCE_TOKENIZER.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=enable_thinking,
    )
    model_inputs = INFERENCE_TOKENIZER([text], return_tensors="pt").to(
        INFERENCE_MODEL.device
    )

    # Generate text using the inference model
    generated_ids = INFERENCE_MODEL.generate(
        **model_inputs, max_new_tokens=max_new_tokens
    )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]) :].tolist()

    # Identify end of the thinking process
    try:
        # rindex finding 151668 (</think>)
        index = len(output_ids) - output_ids[::-1].index(151668)
    except ValueError:
        index = 0

    # Decode the response text (after the thinking process)
    resp = INFERENCE_TOKENIZER.decode(
        output_ids[index:], skip_special_tokens=True
    ).strip("\n")

    # If debugging is enabled, log the thinking content too
    if logger.isEnabledFor(logging.DEBUG):
        thinking_content = INFERENCE_TOKENIZER.decode(
            output_ids[:index], skip_special_tokens=True
        ).strip("\n")
        logger.debug(f"Thinking content: {thinking_content}")

    # Remove inputs and outputs to free up memory
    del output_ids
    del model_inputs
    torch.cuda.empty_cache()

    return resp


def embed_texts(
    input_type: Literal["article", "query"], texts: List[str]
) -> torch.tensor:
    """
    Generate embeddings for the input texts.
    If input_type is 'query', uses the query embedding model and tokenizer, runs on cpu.
    If input_type is 'article', uses the article embedding model, which is loaded dynamically
        on cuda to save memory. Model is deleted after use to free up memory.

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
        # Load article embedding model
        ARTICLE_EMBEDDING_TOKENIZER = AutoTokenizer.from_pretrained(
            CONFIG["ARTICLE_EMBEDDING_MODEL"]
        )
        ARTICLE_EMBEDDING_MODEL = AutoModel.from_pretrained(
            CONFIG["ARTICLE_EMBEDDING_MODEL"], device_map=CONFIG["DEVICE_MAP"]
        )
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
    )

    if input_type == "article":
        inputs = inputs.to("cuda")

    with torch.no_grad():
        outputs = model(**inputs)

    # Use the last hidden state as the embedding
    embeddings = outputs.last_hidden_state.mean(dim=1).cpu()

    # If input_type is 'article', delete the model and tokenizer to free up memory
    if input_type == "article":
        del ARTICLE_EMBEDDING_MODEL
        del ARTICLE_EMBEDDING_TOKENIZER
    del outputs
    del inputs
    torch.cuda.empty_cache()

    return embeddings


def rerank_chunks(query: str, chunks: List[str]) -> torch.tensor:
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
    )

    logits = CROSS_ENCODER_MODEL(**encoded).logits.squeeze(dim=1)

    return logits


def generate_search_query(query: str, chat_history: str) -> str:

    sys_prompt = PROMPTS["system_prompt"]
    search_prompt = PROMPTS["search_prompt"].format(
        chat_history=chat_history, question=query
    )

    prompt = f"{sys_prompt}\n\n{search_prompt}"

    return generate_text(
        prompt,
        enable_thinking=False,
    )
    # messages = [
    #     {"role": "user", "content": prompt},
    # ]

    # outputs = INFERENCE_PIPELINE(messages)

    # messages = outputs[0]["generated_text"]

    # del outputs
    # torch.cuda.empty_cache()

    # return messages[-1]["content"]


def generate_chat_response(query: str, context: str) -> str:

    sys_prompt = PROMPTS["system_prompt"]
    chat_prompt = PROMPTS["chat_prompt"].format(question=query, context=context)

    prompt = f"{sys_prompt}\n\n{chat_prompt}"

    return generate_text(prompt, enable_thinking=True)

    # messages = [
    #     {"role": "user", "content": prompt},
    # ]

    # logger.info(f"Input messages: {messages}")

    # outputs = INFERENCE_PIPELINE(messages)

    # messages = outputs[0]["generated_text"]

    # del outputs
    # torch.cuda.empty_cache()

    # return messages[-1]["content"]
