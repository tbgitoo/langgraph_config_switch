# langgraph_config_switch

Minimal dict-based LLM selection for LangChain/LangGraph, with an internal
preset registry and string-only selectors.

## Public API (stable)
- `get_llm(config_llm, format=None, temperature=0.2)`
- `build_runtime(config_llm, temperature=0.2, format=None, callbacks=())`

## Optional helpers (internal, not exported)
- `resolve_config(llm="ollama", tracer="langfuse", profile="local")`
- `PRESETS` in `presets.py`

## Quick usage (recommended)

```python
from langgraph_config_switch.resolve import resolve_config
from langgraph_config_switch import build_runtime

cfg = resolve_config(llm="ollama", tracer="langfuse", profile="local")
runtime = build_runtime(cfg["config_llm"], callbacks=cfg["callbacks"], temperature=0.2)

llm = runtime.llm
callbacks = runtime.callbacks
print(runtime.provider_label)

```

## Notes

Presets never hardcode secrets. Keys are injected from environment variables.
Tracing callbacks are optional; if not configured, callbacks=().

### License
GPL-3.0-only. See LICENSE.