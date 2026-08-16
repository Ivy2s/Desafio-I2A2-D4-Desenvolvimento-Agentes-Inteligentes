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
    monkeypatch.setattr(config, "GROQ_MODEL", "openai/gpt-oss-20b")
    monkeypatch.setattr(csv_agent, "GROQ_API_KEY", "groq-test-key")

    agent = create_agent()

    assert agent is not None


def test_agent_factory_avoids_groq_retries_by_default(monkeypatch):
    import agents.csv_agent as csv_agent

    captured = {}

    class FakeModel:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def bind_tools(self, tools):
            return self

        def with_structured_output(self, schema, **kwargs):
            captured["schema"] = schema
            captured["structured_output"] = kwargs
            return self

    monkeypatch.setattr(csv_agent, "AI_PROVIDER", "groq")
    monkeypatch.setattr(csv_agent, "GROQ_API_KEY", "groq-test-key")
    monkeypatch.setattr(csv_agent, "GROQ_MODEL", "openai/gpt-oss-20b")
    monkeypatch.setattr(csv_agent, "ChatGroq", FakeModel)
    monkeypatch.setattr(csv_agent, "GROQ_AGENT_RETRIES", 0)

    csv_agent.create_agent()

    assert captured["max_retries"] == 0
    assert captured["max_tokens"] == 256
    assert captured["model"] == "openai/gpt-oss-20b"
    assert captured["reasoning_effort"] == "low"
    assert captured["model_kwargs"] == {"include_reasoning": False}
    assert captured["structured_output"] == {
        "method": "json_schema",
        "strict": True,
        "include_raw": True,
    }
    assert captured["schema"]["parameters"]["additionalProperties"] is False
    limit_variants = captured["schema"]["parameters"]["properties"]["limit"]["anyOf"]
    assert [variant.get("type") for variant in limit_variants] == ["integer", "null"]
