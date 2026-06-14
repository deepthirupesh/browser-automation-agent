"""Tests for LLM provider configuration."""

from __future__ import annotations

from config import Settings


def test_auto_prefers_openrouter_when_key_set() -> None:
    settings = Settings(
        openrouter_api_key="sk-or-test",
        anthropic_api_key="sk-ant-test",
        llm_provider="auto",
        use_mock_llm=False,
    )
    assert settings.resolved_llm_provider == "openrouter"
    assert settings.llm_enabled
    assert settings.llm_model == "anthropic/claude-sonnet-4"


def test_explicit_anthropic_provider() -> None:
    settings = Settings(
        openrouter_api_key="sk-or-test",
        anthropic_api_key="sk-ant-test",
        llm_provider="anthropic",
        use_mock_llm=False,
    )
    assert settings.resolved_llm_provider == "anthropic"
    assert settings.llm_model == "claude-sonnet-4-6"


def test_mock_llm_disables_provider() -> None:
    settings = Settings(
        openrouter_api_key="sk-or-test",
        use_mock_llm=True,
    )
    assert settings.resolved_llm_provider is None
    assert not settings.llm_enabled
