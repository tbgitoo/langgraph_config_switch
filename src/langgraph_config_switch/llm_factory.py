from __future__ import annotations

from typing import Any, Dict, Optional, Union

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


def get_llm(
    config: Dict[str, Any],
    format: Optional[str] = None,
    temperature: float = 0.2,
) -> Union[ChatOpenAI, ChatOllama]:
    """
    Strictly supports:
      - LLM_PROVIDER in {"ollama", "openai"}

    Required keys:
      ollama:
        - OLLAMA_MODEL
        - OLLAMA_BASE_URL
      openai:
        - OPENAI_MODEL
        - OPENAI_API_KEY

    'format' is only passed to Ollama (optional).
    """
    if "LLM_PROVIDER" not in config:
        raise KeyError("Missing required key: LLM_PROVIDER")

    provider = config["LLM_PROVIDER"]  # strict: must exist

    if provider == "ollama":
        for k in ("OLLAMA_MODEL", "OLLAMA_BASE_URL"):
            if k not in config:
                raise KeyError(f"Missing required key for ollama: {k}")

        kwargs = {
            "model": config["OLLAMA_MODEL"],
            "base_url": config["OLLAMA_BASE_URL"],
            "temperature": temperature,
        }
        if format is not None:
            kwargs["format"] = format  # e.g. "json" (if supported by your ChatOllama)
        return ChatOllama(**kwargs)

    if provider == "openai":
        for k in ("OPENAI_MODEL", "OPENAI_API_KEY"):
            if k not in config:
                raise KeyError(f"Missing required key for openai: {k}")

        return ChatOpenAI(
            model=config["OPENAI_MODEL"],
            temperature=temperature,
            api_key=config["OPENAI_API_KEY"],
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER={provider!r}. Expected 'ollama' or 'openai'."
    )