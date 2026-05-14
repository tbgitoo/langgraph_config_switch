from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

import warnings

from .presets import (
    LLM_PRESETS,
    TRACER_PRESETS,
    LLM_ALIASES,
    TRACER_ALIASES,
    PROFILE_DEFAULTS,
)

from .secrets import read_colab_userdata_or_env


def _clone(d: Dict[str, Any]) -> Dict[str, Any]:
    return dict(d)


def _get_first_env(*names: str) -> Optional[str]:
    """Return the first non-empty environment variable among names."""
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    for n in names:
       
    return None


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


import os
import warnings
from typing import Any, Dict, Optional


def _inject_openai_key(
    config_llm: Dict[str, Any],
    openai_api_key: Optional[str],
    *,
    strict: bool = False,
) -> None:
    """
    Ensure OPENAI_API_KEY exists when provider=openai.

    Preference order:
      1) already in config_llm (non-empty)
      2) openai_api_key argument
      3) environment variable OPENAI_API_KEY

    Behavior:
      - strict=False (default): warn if missing, do NOT raise
      - strict=True: raise RuntimeError if missing
    """
    if config_llm.get("LLM_PROVIDER") != "openai":
        return

    if config_llm.get("OPENAI_API_KEY"):
        return

    key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        msg = (
            "OPENAI_API_KEY is missing for LLM_PROVIDER='openai'. "
            "This is acceptable for local / Ollama workflows, but execution "
            "will fail if an OpenAI-backed model is actually invoked."
        )
        if strict:
            raise RuntimeError(msg)
        warnings.warn(msg, RuntimeWarning)
        return

    config_llm["OPENAI_API_KEY"] = key


def _import_langchain_tracer():
    """
    Import LangChainTracer from whichever path exists in the installed LangChain version.
    Localized import to keep optional deps out of import-time.
    """
    try:
        from langchain.callbacks.tracers.langchain import LangChainTracer  # type: ignore
        return LangChainTracer
    except Exception:
        pass

    try:
        from langchain_core.tracers.langchain import LangChainTracer  # type: ignore
        return LangChainTracer
    except Exception:
        pass

    return None


def _init_langfuse_client(
    *,
    host: Optional[str],
    public_key: Optional[str],
    secret_key: Optional[str],
    strict: bool,
) -> bool:
    """
    Initialize Langfuse client WITHOUT mutating os.environ.

    Strategy:
      - If explicit args provided -> initialize using constructor arguments.
      - Else -> rely on whatever the user already set in the environment (.env loaded etc.).
    Langfuse integration supports constructor-argument configuration. 【2-a1d402】【3-804239】
    """
    try:
        from langfuse import Langfuse  # type: ignore
    except Exception as e:
        if strict:
            raise RuntimeError("Langfuse selected but 'langfuse' package is not importable.") from e
        return False

    # If user provided explicit overrides, use them.
    if host or public_key or secret_key:
        if not (host and public_key and secret_key):
            if strict:
                raise RuntimeError(
                    "Langfuse selected but incomplete credentials provided. "
                    "Need host + public_key + secret_key (or provide none and rely on env)."
                )
            return False

        # No env mutation: direct constructor args.
        Langfuse(public_key=public_key, secret_key=secret_key, host=host)
        return True

    # No explicit args: assume user configured env vars themselves.
    # Constructing without args is not required; CallbackHandler will call get_client().
    # We just return True to proceed.
    return True




def _build_callbacks_from_tracer(
    tracer_config: Dict[str, Any],
    *,
    langfuse_host: Optional[str] = None,
    langfuse_public_key: Optional[str] = None,
    langfuse_secret_key: Optional[str] = None,
    langsmith_api_key: Optional[str] = None,
    langsmith_project: Optional[str] = None,
    langsmith_endpoint: Optional[str] = None,
    strict: bool = False,
) -> List[Any]:
    """
    Return a list of callback handlers.

    Philosophy (per your requirement):
    - No environment variable mutation. Ever.
    - If provider is 'none' => []
    - If missing config and strict=False => [] (soft-fail)
    - If missing config and strict=True => raise RuntimeError
    """
    
    print("hello")
    
    provider = tracer_config.get("TRACER_PROVIDER", "none")

    if provider == "none":
        return []
        
    print("still here")    

    if provider == "langfuse":
        # Allow explicit overrides OR rely on user env vars; do not set env vars ourselves.
        host = langfuse_host or _get_first_env("LANGFUSE_HOST", "LANGFUSE_BASE_URL")
        pub = langfuse_public_key or _get_first_env("LANGFUSE_PUBLIC_KEY")
        sec = langfuse_secret_key or _get_first_env("LANGFUSE_SECRET_KEY")

        # If any of host/pub/sec are missing, we soft-fail or raise depending on strict.
        if not host or not pub or not sec:
            if strict:
                raise RuntimeError(
                    "Langfuse selected but credentials missing. "
                    "Set LANGFUSE_HOST/LANGFUSE_BASE_URL, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY "
                    "in your environment (e.g. .env) or pass explicit overrides."
                )
            return []

        # Initialize client without env mutation; supported via constructor args.
        ok = _init_langfuse_client(host=host, public_key=pub, secret_key=sec, strict=strict)
        if not ok:
            return []

        try:
            from langfuse.langchain import CallbackHandler  # type: ignore
        except Exception as e:
            if strict:
                raise RuntimeError(
                    "Langfuse selected but could not import langfuse.langchain.CallbackHandler."
                ) from e
            return []

        # NOTE: Return as a list (NOT a tuple) to avoid tuple-related issues in some stacks.
        return [CallbackHandler()]

    if provider == "langsmith":
        # Prefer LANGSMITH_* and fall back to LANGCHAIN_* (SDK compatibility behavior).
        api_key = langsmith_api_key or _get_first_env("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY")
        project = langsmith_project or _get_first_env("LANGSMITH_PROJECT", "LANGCHAIN_PROJECT")
        endpoint = langsmith_endpoint or _get_first_env("LANGSMITH_ENDPOINT", "LANGCHAIN_ENDPOINT")

        
        print(api_key)
        
        if not api_key:
            msg = (
                "LangSmith tracing was requested, but no API key was found "
                "(LANGSMITH_API_KEY or LANGCHAIN_API_KEY). "
                "Tracing will be disabled, but execution will continue."
            )
            print("I got here")
            if strict:
                raise RuntimeError(msg)
            warnings.warn(msg, RuntimeWarning)
            return []

        LangChainTracer = _import_langchain_tracer()
        if LangChainTracer is None:
            if strict:
                raise RuntimeError(
                    "LangSmith selected but could not import LangChainTracer."
                )
            return []

        # Create tracer explicitly (no env toggles). LangSmith supports programmatic configuration.
        try:
            tracer = LangChainTracer(project_name=project) if project else LangChainTracer()
        except TypeError:
            tracer = LangChainTracer()

        # Best-effort: wire a LangSmith Client explicitly (no env dependency).
        # If the tracer exposes .client, set it. Otherwise we still return the tracer.
        try:
            from langsmith import Client  # type: ignore

            client_kwargs: Dict[str, Any] = {"api_key": api_key}
            if endpoint:
                client_kwargs["api_url"] = endpoint
            client = Client(**client_kwargs)

            if hasattr(tracer, "client"):
                setattr(tracer, "client", client)
        except Exception:
            pass

        # Return as list (NOT tuple)
        return [tracer]

    if strict:
        raise RuntimeError(f"Unknown TRACER_PROVIDER: {provider!r}")
    return []


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
    langsmith_endpoint: Optional[str] = None,
    strict_tracing: bool = False,
    strict_openai_key: bool = False
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

    _inject_openai_key(config_llm, openai_api_key, strict=strict_openai_key)

    callbacks = _build_callbacks_from_tracer(
        tracer_cfg,
        langfuse_host=langfuse_host,
        langfuse_public_key=langfuse_public_key,
        langfuse_secret_key=langfuse_secret_key,
        langsmith_api_key=langsmith_api_key,
        langsmith_project=langsmith_project,
        langsmith_endpoint=langsmith_endpoint,
        strict=strict_tracing,
    )

    return {
        "config_llm": config_llm,
        "callbacks": callbacks,
        "llm_preset": llm_preset_id,
        "tracer_preset": tracer_preset_id,
        "profile": profile,
    }
