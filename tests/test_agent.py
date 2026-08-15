import pytest

from agents.csv_agent import create_agent


def test_agent_factory_requires_key_only_when_called(monkeypatch):
    monkeypatch.setattr("agents.csv_agent.GOOGLE_API_KEY", None)
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        create_agent()
