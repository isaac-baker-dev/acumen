"""Acumen Image Understanding - Analyze images using Moondream vision model."""

import base64
import requests
from pathlib import Path
from acumen.core.config import OLLAMA_BASE_URL
from acumen.core.logger import get_logger

logger = get_logger("acumen.tools.image")

def encode_image(image_path):
    path = Path(image_path)
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def analyze_image(image_path, question="Describe this image in detail."):
    img_b64 = encode_image(image_path)
    if not img_b64:
        return f"Image not found: {image_path}"
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "moondream",
                "prompt": question,
                "images": [img_b64],
                "stream": False
            },
            timeout=180
        )
        result = response.json()
        answer = result.get("response", "No response")
        logger.info(f"Image analyzed: {image_path} - {len(answer)} chars")
        return answer
    except Exception as e:
        logger.warning(f"Image analysis failed: {e}")
        return f"Image analysis failed: {str(e)}"

def analyze_image_bytes(image_bytes, question="Describe this image in detail."):
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "moondream",
                "prompt": question,
                "images": [img_b64],
                "stream": False
            },
            timeout=180
        )
        result = response.json()
        answer = result.get("response", "No response")
        logger.info(f"Image analyzed from bytes - {len(answer)} chars")
        return answer
    except Exception as e:
        logger.warning(f"Image analysis failed: {e}")
        return f"Image analysis failed: {str(e)}"