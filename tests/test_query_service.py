from types import SimpleNamespace

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


def test_query_service_runs_tool_loop_and_returns_table(monkeypatch, tmp_path):
    import services.query_service as query_service

    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
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
    }
    assert fake_tool.calls == [{"operation": "list", "dataset": "dataset"}]
    assert fake_agent.calls[0][0].content.strip().startswith("Você é um agente inteligente")


def test_query_service_enforces_iteration_limit(monkeypatch, tmp_path):
    import services.query_service as query_service

    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
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
