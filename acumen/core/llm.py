"""
Acumen LLM Client - Unified interface for local and cloud models.
Green computing: lazy loading, connection reuse, minimal memory.
Learning loop: cloud responses are saved to local knowledge base.
"""

from langchain_community.llms import Ollama
from acumen.core.config import (
    OLLAMA_BASE_URL, MODELS, is_cloud_available, DEFAULT_TEMP
)
from acumen.core.logger import get_logger

logger = get_logger("acumen.core.llm")

_model_cache = {}

def get_llm(role: str = "reasoning", temperature: float = None,
            num_ctx: int = None, max_tokens: int = 2048):
    from acumen.core.config import DEFAULT_CTX
    temp = temperature if temperature is not None else DEFAULT_TEMP
    ctx = num_ctx or DEFAULT_CTX
    cache_key = f"{role}_{temp}_{ctx}"

    if cache_key in _model_cache:
        return _model_cache[cache_key]

    if role == "cloud":
        if not is_cloud_available():
            logger.warning("No API key. Falling back to local.")
            role = "reasoning"
        else:
            wrapper = CloudLLMWrapper(temp, max_tokens)
            _model_cache[cache_key] = wrapper
            return wrapper

    model_name = MODELS.get(role, MODELS["reasoning"])
    logger.info(f"Loading local model: {model_name} (role: {role})")
    llm = Ollama(model=model_name, base_url=OLLAMA_BASE_URL,
                 temperature=temp, num_ctx=ctx, num_predict=max_tokens)
    _model_cache[cache_key] = llm
    return llm

class CloudLLMWrapper:
    def __init__(self, temperature, max_tokens):
        self.temp = temperature
        self.max_tokens = max_tokens

    def invoke(self, prompt: str) -> str:
        from litellm import completion
        logger.info("Sending to Claude (cloud fallback)")
        r = completion(model="claude-sonnet-4-20250514",
                       messages=[{"role":"user","content":prompt}],
                       temperature=self.temp, max_tokens=self.max_tokens)
        response = r.choices[0].message.content
        try:
            # Only save the response, not the system prompt
            if "You are Acumen" not in response[:100]:
                memory.save_knowledge(
                    f"{response[:1500]}",
                    {"source": "claude", "topic": "learned"}
                )
            memory.save_episode("cloud_learning", prompt[:300],
                {"model": "claude", "response_length": len(response)})
            logger.info("Cloud response saved to local knowledge base")
        except Exception as e:
            logger.warning(f"Could not save cloud response: {e}")
        return response

    def __call__(self, prompt): return self.invoke(prompt)