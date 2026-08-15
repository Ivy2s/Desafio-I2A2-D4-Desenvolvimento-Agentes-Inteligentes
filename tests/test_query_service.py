from types import SimpleNamespace

import pytest

import services.query_service as query_service
from services.exceptions import AgentExecutionError, AgentTimeoutError, ToolExecutionError
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

    assert result.answer == "Consulta concluída"
    assert result.data == {
        "type": "table",
        "columns": ["name", "value"],
        "rows": [{"name": "alpha", "value": "10"}],
        "truncated": False,
        "returnedRows": 1,
    }
    assert fake_tool.calls == [{"operation": "list", "dataset": "dataset"}]
    assert fake_agent.calls[0][0].content.strip().startswith("Você é um agente inteligente")


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

    assert result.answer == "Dados consultados"
    assert describe_calls == [{}]
    assert query_calls == [{"operation": "list", "dataset": "dataset"}]
    assert fake_agent.calls[1][-1].tool_call_id == "describe"
    assert fake_agent.calls[2][-1].tool_call_id == "query"


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

    with pytest.raises(AgentTimeoutError):
        service.query(session.dataset_id, "espere")


def test_query_service_maps_model_failure(monkeypatch, tmp_path):
    fake_agent = SimpleNamespace(
        invoke=lambda messages: (_ for _ in ()).throw(RuntimeError("provider failure"))
    )
    service, session = configured_service(monkeypatch, tmp_path, fake_agent, [])

    with pytest.raises(AgentExecutionError):
        service.query(session.dataset_id, "falhe")


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

        def bind_tools(self, tools):
            return self

    monkeypatch.setattr(csv_agent, "GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr(csv_agent, "ChatGoogleGenerativeAI", FakeModel)

    csv_agent.create_agent()

    assert captured["request_timeout"] > 0
    assert captured["retries"] == 2


def test_query_service_enforces_iteration_limit(monkeypatch, tmp_path):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    fake_tool = FakeTool()
    fake_agent = FakeAgent()
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "build_tools", lambda manager: [fake_tool])
    monkeypatch.setattr(query_service, "create_agent", lambda manager, tools: fake_agent)
    fake_agent.invoke = lambda messages: SimpleNamespace(
        content="", tool_calls=[{"id": "tool", "name": "query_data", "args": {"dataset": "dataset"}}]
    )

    try:
        QueryService(registry, max_iterations=2).query(session.dataset_id, "repita")
    except query_service.AgentIterationLimitError:
        return
    raise AssertionError("O limite de iterações não foi aplicado")
