from types import SimpleNamespace

import pandas as pd
import pytest

import services.query_service as query_service
from services.exceptions import AgentExecutionError, AgentTimeoutError, ToolExecutionError
from services.provider_health import ProviderHealth
from services.query_service import QueryService
from services.session_registry import SessionRegistry


class FakeTool:
    name = "query_data"

    def __init__(self):
        self.calls = []

    def invoke(self, args):
        self.calls.append(args)
        return {
            "dataset": args["dataset"],
            "operation": "list",
            "result": [{"name": "alpha", "value": "10"}],
        }


class FakeAgent:
    def __init__(self):
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        if len(self.calls) == 1:
            return SimpleNamespace(
                content="",
                tool_calls=[
                    {
                        "id": "tool-1",
                        "name": "query_data",
                        "args": {"operation": "list", "dataset": "dataset"},
                    }
                ],
            )
        return SimpleNamespace(content="Consulta concluída", tool_calls=[])


def configured_service(monkeypatch, tmp_path, agent, tools):
    import services.query_service as query_service

    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: tools)
    monkeypatch.setattr(query_service, "create_agent", lambda manager, tools: agent)
    return QueryService(registry), session


def test_query_service_runs_tool_loop_and_returns_table(monkeypatch, tmp_path):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    fake_tool = FakeTool()
    fake_agent = FakeAgent()
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: [fake_tool])
    monkeypatch.setattr(query_service, "create_agent", lambda manager, tools: fake_agent)

    result = QueryService(registry).query(session.dataset_id, "liste os dados")

    assert result.answer == "A consulta retornou 1 resultado(s) na tabela."
    assert result.data == {
        "type": "table",
        "columns": ["name", "value"],
        "rows": [{"name": "alpha", "value": "10"}],
        "truncated": False,
        "returnedRows": 1,
    }
    assert fake_tool.calls == [{"operation": "list", "dataset": "dataset"}]
    assert fake_agent.calls[0][0].content.strip().startswith("Voce e um planejador")


def test_query_service_accepts_direct_model_response(monkeypatch, tmp_path):
    fake_agent = SimpleNamespace(
        calls=[],
        invoke=lambda messages: SimpleNamespace(
            content="Posso analisar os datasets carregados.", tool_calls=[]
        ),
    )
    service, session = configured_service(monkeypatch, tmp_path, fake_agent, [])

    result = service.query(session.dataset_id, "O que você consegue fazer?")

    assert result.answer == "Posso analisar os datasets carregados."
    assert result.data is None


def test_query_service_mentions_all_session_datasets_in_context(monkeypatch, tmp_path):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    session.manager.datasets = {
        "vendas": pd.DataFrame({"valor": [10, 20]}),
        "estoque": pd.DataFrame({"quantidade": [5, 7]}),
    }
    session.manager.dictionary = {
        "vendas": {"columns": ["valor"], "dtypes": {"valor": "int64"}, "descriptions": {}},
        "estoque": {"columns": ["quantidade"], "dtypes": {"quantidade": "int64"}, "descriptions": {}},
    }

    messages = QueryService(registry)._messages(session.manager, "qual foi o total?", "gemini")

    assert "vendas" in messages[0].content.lower()
    assert "estoque" in messages[0].content.lower()
    assert '"vendas"' in messages[0].content.lower()


def test_query_service_runs_describe_then_query(monkeypatch, tmp_path):
    describe = FakeTool()
    describe.name = "describe_data"
    describe_calls = []
    describe.invoke = lambda args: (describe_calls.append(args) or {"dataset": {"columns": ["name"]}})
    query = FakeTool()
    query_calls = []
    original_query = query.invoke
    query.invoke = lambda args: (query_calls.append(args) or original_query(args))
    responses = iter(
        [
            SimpleNamespace(
                content="",
                tool_calls=[{"id": "describe", "name": "describe_data", "args": {}}],
            ),
            SimpleNamespace(
                content="",
                tool_calls=[
                    {
                        "id": "query",
                        "name": "query_data",
                        "args": {"operation": "list", "dataset": "dataset"},
                    }
                ],
            ),
            SimpleNamespace(content="Dados consultados", tool_calls=[]),
        ]
    )
    fake_agent = SimpleNamespace(calls=[])
    fake_agent.invoke = lambda messages: (fake_agent.calls.append(list(messages)) or next(responses))
    query.name = "query_data"
    service, session = configured_service(monkeypatch, tmp_path, fake_agent, [describe, query])

    result = service.query(session.dataset_id, "consulte os dados")

    assert result.answer == "A consulta retornou 1 resultado(s) na tabela."
    assert describe_calls == [{}]
    assert query_calls == [{"operation": "list", "dataset": "dataset"}]
    assert fake_agent.calls[1][-1].tool_call_id == "describe"
    assert len(fake_agent.calls) == 2


def test_query_service_defers_query_emitted_with_describe(monkeypatch, tmp_path):
    describe = FakeTool()
    describe.name = "describe_data"
    describe.invoke = lambda args: {"dataset": {"columns": ["name", "value"]}}
    query = FakeTool()
    query_calls = []
    query.invoke = lambda args: (query_calls.append(args) or {
        "operation": "list",
        "result": [{"name": "alpha", "value": "10"}],
    })
    responses = iter([
        SimpleNamespace(content="", tool_calls=[
            {"id": "describe", "name": "describe_data", "args": {}},
            {"id": "premature", "name": "query_data", "args": {"dataset": "invented"}},
        ]),
        SimpleNamespace(content="", tool_calls=[
            {"id": "query", "name": "query_data", "args": {"operation": "list", "dataset": "dataset"}},
        ]),
        SimpleNamespace(content="Consulta concluída", tool_calls=[]),
    ])
    fake_agent = SimpleNamespace(calls=[])
    fake_agent.invoke = lambda messages: (fake_agent.calls.append(list(messages)) or next(responses))
    query.name = "query_data"
    service, session = configured_service(monkeypatch, tmp_path, fake_agent, [describe, query])

    result = service.query(session.dataset_id, "consulte os dados")

    assert result.answer == "A consulta retornou 1 resultado(s) na tabela."
    assert query_calls == [{"operation": "list", "dataset": "dataset"}]


def test_query_service_rejects_unknown_tool(monkeypatch, tmp_path):
    fake_agent = SimpleNamespace(
        invoke=lambda messages: SimpleNamespace(
            content="",
            tool_calls=[{"id": "bad", "name": "delete_everything", "args": {}}],
        )
    )
    service, session = configured_service(monkeypatch, tmp_path, fake_agent, [])

    with pytest.raises(query_service.UnknownToolError):
        service.query(session.dataset_id, "apague tudo")


def test_query_service_wraps_invalid_tool_arguments(monkeypatch, tmp_path):
    tool = FakeTool()
    tool.invoke = lambda args: (_ for _ in ()).throw(ValueError("invalid args"))
    fake_agent = SimpleNamespace(
        invoke=lambda messages: SimpleNamespace(
            content="",
            tool_calls=[{"id": "query", "name": "query_data", "args": {}}],
        )
    )
    service, session = configured_service(monkeypatch, tmp_path, fake_agent, [tool])

    with pytest.raises(ToolExecutionError):
        service.query(session.dataset_id, "consulta inválida")


def test_query_service_maps_model_timeout(monkeypatch, tmp_path):
    fake_agent = SimpleNamespace(invoke=lambda messages: (_ for _ in ()).throw(TimeoutError()))
    service, session = configured_service(monkeypatch, tmp_path, fake_agent, [])
    monkeypatch.setattr(query_service, "GROQ_API_KEY", None)

    with pytest.raises(AgentTimeoutError):
        service.query(session.dataset_id, "espere")


def test_query_service_maps_model_failure(monkeypatch, tmp_path):
    fake_agent = SimpleNamespace(
        invoke=lambda messages: (_ for _ in ()).throw(RuntimeError("provider failure"))
    )
    service, session = configured_service(monkeypatch, tmp_path, fake_agent, [])
    monkeypatch.setattr(query_service, "GROQ_API_KEY", None)

    with pytest.raises(AgentExecutionError):
        service.query(session.dataset_id, "falhe")


def test_query_service_falls_back_when_primary_agent_cannot_start(monkeypatch, tmp_path):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    fallback_agent = SimpleNamespace(
        invoke=lambda messages: SimpleNamespace(content="Resposta Groq", tool_calls=[])
    )
    providers = []

    def create_agent(manager, tools, provider=None):
        providers.append(provider)
        if provider is None:
            raise RuntimeError("Gemini key not configured")
        return fallback_agent

    monkeypatch.setattr(query_service, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(query_service, "GROQ_API_KEY", "groq-test-key")
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: [])
    monkeypatch.setattr(query_service, "create_agent", create_agent)

    result = QueryService(registry).query(session.dataset_id, "consulte os dados")

    assert result.answer == "Resposta Groq"
    assert providers == [None, "groq"]


def test_query_service_does_not_fallback_for_non_provider_errors(monkeypatch, tmp_path):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    providers = []

    def create_agent(manager, tools, provider=None):
        providers.append(provider)
        return SimpleNamespace(
            invoke=lambda messages: (_ for _ in ()).throw(ValueError("invalid request"))
        )

    monkeypatch.setattr(query_service, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(query_service, "GROQ_API_KEY", "groq-test-key")
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: [])
    monkeypatch.setattr(query_service, "create_agent", create_agent)

    with pytest.raises(AgentExecutionError):
        QueryService(registry).query(session.dataset_id, "consulte os dados")

    assert providers == [None]


def test_query_service_exposes_rate_limit_wait_time(monkeypatch, tmp_path):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    class RateLimitError(RuntimeError):
        status_code = 429

    fake_agent = SimpleNamespace(
        invoke=lambda messages: (_ for _ in ()).throw(
            RateLimitError("rate_limit_exceeded; try again in 6.98s")
        )
    )

    monkeypatch.setattr(query_service, "AI_PROVIDER", "groq")
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: [])
    monkeypatch.setattr(query_service, "create_agent", lambda manager, tools: fake_agent)

    with pytest.raises(query_service.ProviderRateLimitError, match="7s"):
        QueryService(registry).query(session.dataset_id, "consulte os dados")


def test_rate_limit_headers_are_exposed_and_cooldown_skips_provider(monkeypatch, tmp_path):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    now = [0.0]
    health = ProviderHealth(clock=lambda: now[0])
    calls = []

    class RateLimitError(RuntimeError):
        status_code = 429
        headers = {
            "retry-after": "3",
            "x-ratelimit-limit-tokens": "1000",
            "x-ratelimit-remaining-tokens": "0",
            "x-ratelimit-reset-tokens": "3s",
        }

    fake_agent = SimpleNamespace(
        invoke=lambda messages: (_ for _ in ()).throw(RateLimitError("tpm"))
    )

    def create_agent(manager, tools, provider=None):
        calls.append(provider)
        return fake_agent

    monkeypatch.setattr(query_service, "AI_PROVIDER", "groq")
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: [])
    monkeypatch.setattr(query_service, "create_agent", create_agent)
    service = QueryService(registry, provider_health=health)

    with pytest.raises(query_service.ProviderRateLimitError) as first:
        service.query(session.dataset_id, "consulte os dados")
    assert first.value.retry_after_seconds == 3
    assert first.value.metadata["remaining_tokens"] == "0"

    with pytest.raises(query_service.ProviderRateLimitError) as second:
        service.query(session.dataset_id, "consulte os dados novamente")
    assert second.value.retry_after_seconds == 3
    assert calls == [None]

    now[0] = 3.1
    with pytest.raises(query_service.ProviderRateLimitError):
        service.query(session.dataset_id, "consulte os dados após cooldown")
    assert calls == [None, None]


def test_primary_provider_cooldown_uses_fallback_without_retrying_primary(
    monkeypatch, tmp_path
):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    now = [0.0]
    health = ProviderHealth(clock=lambda: now[0])
    providers = []

    class UnavailableError(RuntimeError):
        status_code = 503

    fallback_agent = SimpleNamespace(
        invoke=lambda messages: SimpleNamespace(content="Resposta Groq", tool_calls=[])
    )

    def create_agent(manager, tools, provider=None):
        providers.append(provider)
        if provider is None:
            raise UnavailableError("service unavailable")
        return fallback_agent

    monkeypatch.setattr(query_service, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(query_service, "GROQ_API_KEY", "groq-test-key")
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: [])
    monkeypatch.setattr(query_service, "create_agent", create_agent)
    service = QueryService(registry, provider_health=health)

    assert service.query(session.dataset_id, "primeira").answer == "Resposta Groq"
    assert service.query(session.dataset_id, "segunda").answer == "Resposta Groq"
    assert providers == [None, "groq", "groq"]


def test_model_usage_is_logged_without_prompt_or_secret(monkeypatch, tmp_path, caplog):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    fake_agent = SimpleNamespace(
        invoke=lambda messages: SimpleNamespace(
            content="Resposta",
            tool_calls=[],
            usage_metadata={"input_tokens": 12, "output_tokens": 5, "total_tokens": 17},
        )
    )
    monkeypatch.setattr(query_service, "AI_PROVIDER", "groq")
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: [])
    monkeypatch.setattr(query_service, "create_agent", lambda manager, tools: fake_agent)

    with caplog.at_level("INFO"):
        QueryService(registry).query(session.dataset_id, "pergunta-secreta")

    record = " ".join(caplog.messages)
    assert "provider=groq" in record
    assert "input_tokens=12" in record
    assert "output_tokens=5" in record
    assert "pergunta-secreta" not in record


@pytest.mark.parametrize(
    ("operation", "value", "data_type"),
    [("count", 2, "count"), ("list", [{"name": "Alice"}], "table"), ("aggregate", [{"name": "Alice", "total": 2}], "table")],
)
def test_structured_tool_result_is_preserved(operation, value, data_type):
    data = QueryService._result_as_data({"operation": operation, "result": value})
    assert data["type"] == data_type
    if data_type == "table":
        assert data["rows"] == value
    else:
        assert data["value"] == value


def test_agent_factory_configures_timeout_and_retries(monkeypatch):
    import agents.csv_agent as csv_agent

    captured = {}

    class FakeModel:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def with_structured_output(self, schema, **kwargs):
            captured["schema"] = schema
            captured["structured_output"] = kwargs
            return self

    monkeypatch.setattr(csv_agent, "GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr(csv_agent, "ChatGoogleGenerativeAI", FakeModel)

    csv_agent.create_agent()

    assert captured["request_timeout"] > 0
    assert captured["retries"] == 0
    assert captured["max_tokens"] == 512
    assert captured["thinking_budget"] == 0
    assert captured["schema"].__name__ == "DataQuery"
    assert captured["structured_output"] == {
        "method": "json_schema",
        "include_raw": True,
    }


def test_query_service_enforces_iteration_limit(monkeypatch, tmp_path):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    fake_tool = FakeTool()
    fake_tool.name = "describe_data"
    fake_tool.invoke = lambda args: {"dataset": {"columns": []}}
    fake_agent = FakeAgent()
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: [fake_tool])
    monkeypatch.setattr(query_service, "create_agent", lambda manager, tools: fake_agent)
    fake_agent.invoke = lambda messages: SimpleNamespace(
        content="", tool_calls=[{"id": "tool", "name": "describe_data", "args": {}}]
    )

    try:
        QueryService(registry, max_iterations=2).query(session.dataset_id, "repita")
    except query_service.AgentIterationLimitError:
        return
    raise AssertionError("O limite de iterações não foi aplicado")
