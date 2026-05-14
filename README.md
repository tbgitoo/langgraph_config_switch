# langgraph_config_switch

Minimal, dict-based LLM and tracer selection for LangChain / LangGraph.

The package provides a small abstraction layer that:
- resolves string-based switches (LLM, tracer, profile) into concrete configs
- keeps presets declarative and secret-free
- cleanly separates **configuration** from **execution**
- works identically in local environments and Google Colab

---

## Design principles

- **String-only selectors** for LLMs and tracers
- **Preset registry** (no secrets hardcoded)
- **No hidden side effects** (no environment mutation)
- **Permissive configuration**, **strict execution**
- **Tracer support is optional** and soft-fails with warnings

---

## Public API (stable)

### Configuration
- `resolve_config(...)`

### Execution
- `get_llm(config_llm, format=None, temperature=0.2)`
- `build_runtime(config_llm, callbacks=None, temperature=0.2, format=None)`

---

## Execution model (important)

The package intentionally separates concerns into two phases:

### 1) Configuration (permissive)
`resolve_config(...)`:
- resolves presets and aliases
- injects secrets if available
- allows missing keys (soft-fail)
- emits warnings if tracers are requested but not configured
- produces a portable configuration that can be reused across environments

### 2) Execution (strict)
`get_llm(...)` and `build_runtime(...)`:
- instantiate the actual LLM and runtime
- validate provider-specific requirements
- fail explicitly if required keys are missing

This allows the same configuration to be used locally (e.g. Ollama)
and in cloud environments (e.g. OpenAI) without modification.

---

## Quick usage (recommended)

```python
from langgraph_config_switch.resolve import resolve_config
from langgraph_config_switch import build_runtime

cfg = resolve_config(
    llm="ollama",
    tracer="langsmith",
    profile="local",
)

runtime = build_runtime(
    cfg["config_llm"],
    callbacks=cfg["callbacks"],
    temperature=0.2,
)

llm = runtime.llm
callbacks = runtime.callbacks

print(runtime.provider_label)