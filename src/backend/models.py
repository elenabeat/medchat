import logging
from datetime import datetime

from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModel,
)
import toml

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

# Load query embedding model
QUERY_EMBEDDING_TOKENIZER = AutoTokenizer.from_pretrained(CONFIG["EMBEDDING_MODEL"])
EMBEDDING_MODEL = AutoModel.from_pretrained(CONFIG["EMBEDDING_MODEL"])

# Load article embedding model
ARTICLE_EMBEDDING_TOKENIZER = AutoTokenizer.from_pretrained(
    CONFIG["ARTICLE_EMBEDDING_MODEL"]
)
ARTICLE_EMBEDDING_MODEL = AutoModel.from_pretrained(CONFIG["ARTICLE_EMBEDDING_MODEL"])

# Load cross-encoder model
CROSS_ENCODER_TOKENIZER = AutoTokenizer.from_pretrained(CONFIG["CROSS_ENCODER_MODEL"])
CROSS_ENCODER_MODEL = AutoModel.from_pretrained(CONFIG["CROSS_ENCODER_MODEL"])
