import pytest

from agents.csv_agent import create_agent


def test_agent_factory_requires_key_only_when_called(monkeypatch):
    monkeypatch.setattr("agents.csv_agent.GOOGLE_API_KEY", None)
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        create_agent()


def test_agent_factory_selects_alternative_model_and_key(monkeypatch):
    import agents.csv_agent as csv_agent

    monkeypatch.setattr(csv_agent, "GEMINI_PROFILE", "alternative", raising=False)
    monkeypatch.setattr(csv_agent, "GOOGLE_API_KEY_ALT", "alternative-key", raising=False)
    monkeypatch.setattr(csv_agent, "GEMINI_MODEL_ALT", "gemini-3.5-flash", raising=False)

    key, model = csv_agent._selected_credentials()

    assert (key, model) == ("alternative-key", "gemini-3.5-flash")
