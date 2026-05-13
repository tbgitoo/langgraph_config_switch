from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

from .presets import (
    LLM_PRESETS,
    TRACER_PRESETS,
    LLM_ALIASES,
    TRACER_ALIASES,
    PROFILE_DEFAULTS,
)


def _clone(d: Dict[str, Any]) -> Dict[str, Any]:
    return dict(d)


def _resolve_llm_preset_id(llm: Optional[str], profile: str) -> str:
    """
    Resolve a user-facing llm switch/preset into a concrete preset id.
    Accepts:
      - preset id (exact key in LLM_PRESETS)
      - alias (key in LLM_ALIASES)
      - None: use PROFILE_DEFAULTS[profile]["llm"] then resolve
    """
    if llm is None:
        llm = PROFILE_DEFAULTS.get(profile, {}).get("llm", "ollama")

    if llm in LLM_PRESETS:
        return llm

    if llm in LLM_ALIASES:
        return LLM_ALIASES[llm]

    raise ValueError(f"Unknown llm switch/preset: {llm!r}")


def _resolve_tracer_preset_id(tracer: Optional[str], profile: str) -> str:
    """
    Resolve a user-facing tracer switch/preset into a concrete preset id.
    Accepts:
      - preset id (exact key in TRACER_PRESETS)
      - alias (key in TRACER_ALIASES)
      - None: use PROFILE_DEFAULTS[profile]["tracer"] then resolve
    """
    if tracer is None:
        tracer = PROFILE_DEFAULTS.get(profile, {}).get("tracer", "none")

    if tracer in TRACER_PRESETS:
        return tracer

    if tracer in TRACER_ALIASES:
        return TRACER_ALIASES[tracer]

    raise ValueError(f"Unknown tracer switch/preset: {tracer!r}")


def _inject_openai_key(config_llm: Dict[str, Any], openai_api_key: Optional[str]) -> None:
    """
    Ensure OPENAI_API_KEY exists when provider=openai.
    Preference order:
      1) already in config_llm (non-empty)
      2) openai_api_key argument
      3) environment variable OPENAI_API_KEY
    """
    if config_llm.get("LLM_PROVIDER") != "openai":
        return

    if config_llm.get("OPENAI_API_KEY"):
        return

    key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for LLM_PROVIDER='openai' but was not provided."
        )
    config_llm["OPENAI_API_KEY"] = key


def _build_callbacks_from_tracer(
    tracer_config: Dict[str, Any],
    *,
    langfuse_host: Optional[str] = None,
    langfuse_public_key: Optional[str] = None,
    langfuse_secret_key: Optional[str] = None,
    langsmith_api_key: Optional[str] = None,
    langsmith_project: Optional[str] = None,
    strict: bool = False,
) -> Tuple[Any, ...]:
    """
    Return a tuple of callback handlers.

    Philosophy:
    - If provider is 'none' => ()
    - For langfuse/langsmith: configure from explicit args or env vars.
    - If missing config and strict=False => () (soft-fail)
    - If missing config and strict=True => raise RuntimeError
    """
    provider = tracer_config.get("TRACER_PROVIDER", "none")

    if provider == "none":
        return ()

    if provider == "langfuse":
        host = langfuse_host or os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL")
        pub = langfuse_public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        sec = langfuse_secret_key or os.getenv("LANGFUSE_SECRET_KEY")

        if not host or not pub or not sec:
            if strict:
                raise RuntimeError(
                    "Langfuse selected but LANGFUSE_HOST/LANGFUSE_BASE_URL, "
                    "LANGFUSE_PUBLIC_KEY, or LANGFUSE_SECRET_KEY missing."
                )
            return ()

        # Ensure env vars exist for the handler/client (CallbackHandler reads env vars)
        os.environ.setdefault("LANGFUSE_HOST", host)
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", pub)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", sec)

        try:
            # Correct Langfuse LangChain integration import
            from langfuse.langchain import CallbackHandler  # type: ignore
        except Exception as e:
            if strict:
                raise RuntimeError(
                    "Langfuse selected but could not import langfuse.langchain.CallbackHandler."
                ) from e
            return ()

        return (CallbackHandler(),)
   
    if provider == "langsmith":
        # Many setups rely on env vars + LangChain internal tracing; no explicit callback needed.
        api_key = langsmith_api_key or os.getenv("LANGCHAIN_API_KEY")
        project = (
            langsmith_project
            or os.getenv("LANGCHAIN_PROJECT")
            or os.getenv("LANGSMITH_PROJECT")
        )

        if not api_key:
            if strict:
                raise RuntimeError("LangSmith selected but LANGCHAIN_API_KEY missing.")
            return ()

        # LangChain typically reads these environment variables
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", api_key)
        if project:
            os.environ.setdefault("LANGCHAIN_PROJECT", project)

        # Returning empty tuple is fine: tracing is enabled via env vars
        return ()

    # Unknown tracer provider
    if strict:
        raise RuntimeError(f"Unknown TRACER_PROVIDER: {provider!r}")
    return ()


def resolve_config(
    *,
    llm: Optional[str] = None,
    tracer: Optional[str] = None,
    profile: str = "local",
    openai_api_key: Optional[str] = None,
    # tracer overrides (optional)
    langfuse_host: Optional[str] = None,
    langfuse_public_key: Optional[str] = None,
    langfuse_secret_key: Optional[str] = None,
    langsmith_api_key: Optional[str] = None,
    langsmith_project: Optional[str] = None,
    strict_tracing: bool = False,
) -> Dict[str, Any]:
    """
    Resolve simple string switches into:
      - config_llm (dict) suitable for get_llm/build_runtime
      - callbacks (tuple)

    Switches:
      llm: "ollama" | "openai" | or explicit preset id
      tracer: "langfuse" | "langsmith" | "none" | or explicit preset id
      profile: "local" | "cloud" (controls defaults if llm/tracer omitted)
    """
    llm_preset_id = _resolve_llm_preset_id(llm, profile)
    tracer_preset_id = _resolve_tracer_preset_id(tracer, profile)

    config_llm = _clone(LLM_PRESETS[llm_preset_id])
    tracer_cfg = _clone(TRACER_PRESETS[tracer_preset_id])

    # Inject secrets as needed
    _inject_openai_key(config_llm, openai_api_key)

    callbacks = _build_callbacks_from_tracer(
        tracer_cfg,
        langfuse_host=langfuse_host,
        langfuse_public_key=langfuse_public_key,
        langfuse_secret_key=langfuse_secret_key,
        langsmith_api_key=langsmith_api_key,
        langsmith_project=langsmith_project,
        strict=strict_tracing,
    )

    return {
        "config_llm": config_llm,
        "callbacks": callbacks,
        "llm_preset": llm_preset_id,
        "tracer_preset": tracer_preset_id,
        "profile": profile,
    }