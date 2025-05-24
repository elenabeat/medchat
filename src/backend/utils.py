from typing import Dict, Any
import logging

import requests

logger = logging.getLogger(__name__)


def get_model_config() -> Dict[str, Any]:

    resp = requests.get(
        url="http://medchat-model:9090/model_details/",
    )

    logger.info(f"Model Details: {resp.json()}")

    return resp.json()
