from __future__ import annotations

"""
Preset registry for LLM and tracer configurations.

Philosophy:
- Define multiple *possibilities* (e.g., Ollama llama3.1:8b, OpenAI gpt-5.4-nano)
- Provide very simple string switches (llm="ollama", tracer="langfuse")
- Do NOT hardcode secrets; resolve them from env in resolve.py
"""

# ---- LLM preset definitions (no secrets embedded) ----

LLM_PRESETS: dict[str, dict] = {
    # Local default
    "ollama_llama3_1_8b": {
        "LLM_PROVIDER": "ollama",
        "OLLAMA_MODEL": "llama3.1:8b",
        "OLLAMA_BASE_URL": "http://localhost:11434",
    },
    # Cloud default (API key injected at resolve-time)
    "openai_gpt_5_4_nano": {
        "LLM_PROVIDER": "openai",
        "OPENAI_MODEL": "gpt-5.4-nano",
        # OPENAI_API_KEY intentionally omitted here
    },
}

# ---- Tracer presets (resolved to callbacks later) ----

TRACER_PRESETS: dict[str, dict] = {
    "none": {"TRACER_PROVIDER": "none"},

    # Langfuse (keys injected from env)
    "langfuse_default": {
        "TRACER_PROVIDER": "langfuse",
        # e.g. LANGFUSE_HOST / LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are env-driven
    },

    # LangSmith (env-driven)
    "langsmith_default": {
        "TRACER_PROVIDER": "langsmith",
        # e.g. LANGCHAIN_API_KEY, LANGCHAIN_TRACING_V2, LANGCHAIN_PROJECT are env-driven
    },
}

# ---- Simple aliases (string-only switches) ----

LLM_ALIASES: dict[str, str] = {
    "ollama": "ollama_llama3_1_8b",
    "openai": "openai_gpt_5_4_nano",
}

TRACER_ALIASES: dict[str, str] = {
    "none": "none",
    "langfuse": "langfuse_default",
    "langsmith": "langsmith_default",
}

# ---- Profile defaults (so you can say profile="local") ----

PROFILE_DEFAULTS: dict[str, dict[str, str]] = {
    "local": {
        "llm": "ollama",
        "tracer": "langfuse",
    },
    "cloud": {
        "llm": "openai",
        "tracer": "langsmith",
    },
}