# langgraph_config_switch

A tiny helper library for LangGraph/LangChain projects that need a minimal
local-vs-cloud LLM switch based on a dict config.

Public API:
- `get_llm(config_llm, format=None, temperature=0.2)`
- `build_runtime(config_llm, temperature=0.2, format=None, callbacks=())`

Supported providers via `config_llm["LLM_PROVIDER"]`:
- `"ollama"`
- `"openai"`

Usage (Ollama local)

from langgraph_config_switch import get_llm, build_runtime

config_llm = {
  "LLM_PROVIDER": "ollama",
  "OLLAMA_MODEL": "llama3.1:8b",
  "OLLAMA_BASE_URL": "http://localhost:11434",
}

llm = get_llm(config_llm, format="json", temperature=0.2)
rt = build_runtime(config_llm, temperature=0.2, format="json")
print(rt.provider_label)


Usage (Open ai)

from langgraph_config_switch import build_runtime

config_llm = {
  "LLM_PROVIDER": "openai",
  "OPENAI_MODEL": "gpt-5.4-nano",
  "OPENAI_API_KEY": "YOUR_KEY",
}

rt = build_runtime(config_llm, temperature=0.2)