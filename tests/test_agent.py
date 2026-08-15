import pytest

from agents.csv_agent import create_agent


def test_agent_factory_requires_primary_key_only_when_called(monkeypatch):
    monkeypatch.setattr("agents.csv_agent.GOOGLE_API_KEY", None)
    monkeypatch.setattr("agents.csv_agent.AI_PROVIDER", "gemini")
    with pytest.raises(RuntimeError, match="gemini"):
        create_agent()


def test_agent_factory_supports_groq_fallback(monkeypatch):
    import agents.csv_agent as csv_agent
    import services.config as config

    monkeypatch.setattr(csv_agent, "AI_PROVIDER", "groq")
    monkeypatch.setattr(config, "GROQ_API_KEY", "groq-test-key")
    monkeypatch.setattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.setattr(csv_agent, "GROQ_API_KEY", "groq-test-key")

    agent = create_agent()

    assert agent is not None
