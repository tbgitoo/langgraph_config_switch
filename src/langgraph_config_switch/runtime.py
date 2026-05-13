from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .llm_factory import get_llm


@dataclass(frozen=True)
class LLMRuntime:
    """
    Minimal runtime container.

    - config_llm: original dict config (useful for auditing/debugging)
    - llm: instantiated ChatOpenAI or ChatOllama
    - callbacks: optional callback handlers (e.g., Langfuse handler(s))
    - provider_label: helpful string like "ollama:llama3.1:8b"
    """
    config_llm: Dict[str, Any]
    llm: Any
    callbacks: Tuple[Any, ...] = ()
    provider_label: str = ""


def build_runtime(
    config_llm: Dict[str, Any],
    *,
    temperature: float = 0.2,
    format: Optional[str] = None,
    callbacks: Tuple[Any, ...] = (),
) -> LLMRuntime:
    """
    Build a minimal runtime from a dict config.

    Intentionally does NOT:
      - load dotenv
      - decide local vs cloud
      - build Langfuse handlers

    Those belong in your notebook/FastAPI entrypoint or another helper layer.
    """
    llm = get_llm(config_llm, format=format, temperature=temperature)

    provider = config_llm.get("LLM_PROVIDER", "?")
    model = config_llm.get("OLLAMA_MODEL") or config_llm.get("OPENAI_MODEL") or "?"
    label = f"{provider}:{model}"

    return LLMRuntime(
        config_llm=config_llm,
        llm=llm,
        callbacks=callbacks,
        provider_label=label,
    )