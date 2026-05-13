import pytest
from langgraph_config_switch import get_llm


def test_missing_provider_raises():
    with pytest.raises(KeyError):
        get_llm({})


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_llm({"LLM_PROVIDER": "banana"})


def test_ollama_missing_keys():
    with pytest.raises(KeyError):
        get_llm({"LLM_PROVIDER": "ollama"})


def test_openai_missing_keys():
    with pytest.raises(KeyError):
        get_llm({"LLM_PROVIDER": "openai", "OPENAI_MODEL": "gpt-5.4-nano"})