from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pandas as pd
import pytest

from services.provider_health import ProviderHealth
from services.query_service import QueryService
from services.session_registry import SessionRegistry
from services.config import GROQ_MAX_COMPLETION_TOKENS
from tools.data_tools import DataQuery


def test_reset_parser_accepts_provider_durations_and_rejects_invalid_values():
    assert QueryService._retry_after_seconds({"retry-after": "1m30s"}, "") == 90
    assert QueryService._retry_after_seconds({"retry-after": "2.5s"}, "") == 3
    assert QueryService._retry_after_seconds({"retry-after": "7.66s"}, "") == 8
    assert QueryService._retry_after_seconds({"retry-after": "45.18s"}, "") == 46
    assert QueryService._retry_after_seconds({"retry-after": "1m2.5s"}, "") == 63
    assert QueryService._retry_after_seconds({"retry-after": "2m59.56s"}, "") == 180
    assert QueryService._retry_after_seconds({"retry-after": "817ms"}, "") == 1
    assert QueryService._retry_after_seconds({"retry-after": "not-a-duration"}, "") is None
    assert QueryService._retry_after_seconds({}, "try again in 4.2s") == 5


def test_groq_completion_limit_keeps_safe_json_margin():
    assert GROQ_MAX_COMPLETION_TOKENS >= 256


def test_provider_health_budget_reservation_is_atomic_under_concurrency():
    health = ProviderHealth(max_concurrent_requests=1)
    health.update_budget("groq", remaining_tokens=100)

    def reserve():
        return health.reserve("groq", 30)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: reserve(), range(8)))

    assert sum(result is not None for result in results) == 3
    assert health.budget("groq")["remaining_tokens"] == 10


def test_half_open_probe_returns_to_closed_after_success():
    now = [0.0]
    health = ProviderHealth(clock=lambda: now[0])
    health.cooldown("groq", 5)
    now[0] = 5.1

    assert health.state("groq") == health.HALF_OPEN
    with health.request("groq"):
        pass
    health.mark_success("groq")
    assert health.state("groq") == health.CLOSED


def test_budget_is_scoped_by_provider_and_model():
    health = ProviderHealth()
    health.update_budget("groq", "llama-3.1-8b-instant", remaining_tokens=0)

    assert health.reserve("groq", 10, "llama-3.1-8b-instant") is None
    assert health.reserve("groq", 10, "openai/gpt-oss-20b") is not None


def test_circuit_is_scoped_by_provider_and_model():
    health = ProviderHealth()
    health.cooldown("groq", 30, "llama-3.1-8b-instant")

    assert health.state("groq", "llama-3.1-8b-instant") == health.OPEN
    assert health.state("groq", "openai/gpt-oss-20b") == health.CLOSED


def test_reservation_success_reconciles_estimate_once():
    health = ProviderHealth()
    health.update_budget("groq", "model", remaining_tokens=100)

    reservation = health.reserve("groq", 30, "model")
    health.reconcile(reservation, actual_tokens=20)
    health.reconcile(reservation, actual_tokens=20)

    assert health.budget("groq", "model")["remaining_tokens"] == 80


def test_reservation_failure_releases_estimate():
    health = ProviderHealth()
    health.update_budget(
        "groq", "model", remaining_tokens=100, remaining_requests=3
    )

    reservation = health.reserve("groq", 30, "model")
    health.reconcile(reservation, release=True)

    budget = health.budget("groq", "model")
    assert budget["remaining_tokens"] == 100
    assert budget["remaining_requests"] == 3


def test_provider_429_authoritative_budget_does_not_double_decrement():
    health = ProviderHealth()
    health.update_budget("groq", "model", remaining_tokens=100)
    reservation = health.reserve("groq", 30, "model")

    health.update_budget("groq", "model", remaining_tokens=0)
    health.reconcile(reservation, release=True, authoritative_tokens=True)

    assert health.budget("groq", "model")["remaining_tokens"] == 0


def test_expired_budget_reset_allows_a_clean_probe():
    now = [0.0]
    health = ProviderHealth(clock=lambda: now[0])
    health.update_budget(
        "groq",
        "model",
        remaining_tokens=0,
        token_reset="7.66s",
        token_reset_seconds=8,
    )
    assert health.reserve("groq", 1, "model") is None

    now[0] = 8.1

    assert health.reserve("groq", 1, "model") is not None


def test_groq_planner_prompt_is_compact_and_has_no_data_rows(tmp_path):
    class Manager:
        def planner_context(self):
            return {"items": {"columns": ["produto", "quantidade"], "types": {"quantidade": "int64"}, "descriptions": {}}}

    messages = QueryService._messages(Manager(), "qual produto vendeu mais?", "groq")
    prompt = messages[0].content
    assert "produto" in prompt
    assert "quantidade" in prompt
    assert "DataFrame" not in prompt
    assert "rows" not in prompt
    assert "qual produto vendeu mais?" == messages[1].content


def test_groq_normal_query_uses_one_generation(monkeypatch, tmp_path):
    import services.query_service as module

    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    calls = []

    class Tool:
        name = "query_data"

        def invoke(self, args):
            return {"operation": "count", "result": 3}

    class Agent:
        def invoke(self, messages):
            calls.append(messages)
            return SimpleNamespace(
                content="",
                tool_calls=[{"id": "q", "name": "query_data", "args": {"operation": "count", "dataset": "items"}}],
                usage_metadata={"input_tokens": 20, "output_tokens": 8, "total_tokens": 28},
            )

    monkeypatch.setattr(module, "AI_PROVIDER", "groq")
    monkeypatch.setattr(module, "is_ai_configured", lambda: True)
    monkeypatch.setattr(module, "build_tools", lambda manager, provider=None: [Tool()])
    monkeypatch.setattr(module, "create_agent", lambda manager, tools, provider=None: Agent())

    result = QueryService(registry).query(session.dataset_id, "quantos registros existem?")

    assert result.data == {"type": "count", "value": 3}
    assert len(calls) == 1


def test_groq_strict_structured_plan_uses_one_generation(monkeypatch, tmp_path):
    import services.query_service as module

    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    registry.register(session)
    calls = []

    class Tool:
        name = "query_data"

        def invoke(self, args):
            return {"operation": "count", "result": 4}

    raw = SimpleNamespace(
        usage_metadata={"input_tokens": 30, "output_tokens": 10, "total_tokens": 40},
        response_metadata={},
        tool_calls=[],
    )
    agent = SimpleNamespace(
        invoke=lambda messages: (
            calls.append(messages)
            or {
                "raw": raw,
                "parsed": {"operation": "count", "dataset": "items"},
                "parsing_error": None,
            }
        )
    )
    monkeypatch.setattr(module, "AI_PROVIDER", "groq")
    monkeypatch.setattr(module, "is_ai_configured", lambda: True)
    monkeypatch.setattr(module, "build_tools", lambda manager, provider=None: [Tool()])
    monkeypatch.setattr(module, "create_agent", lambda manager, tools, provider=None: agent)

    result = QueryService(registry).query(session.dataset_id, "quantos registros?")

    assert result.data == {"type": "count", "value": 4}
    assert result.telemetry["groq_calls"] == 1
    assert result.telemetry["total_tokens"] == 40
    assert len(calls) == 1


@pytest.mark.parametrize(
    "plan",
    [
        {"operation": "count", "dataset": "items"},
        {"operation": "list", "dataset": "items", "sort": "produto", "sort_direction": "asc", "limit": 5},
        {"operation": "aggregate", "dataset": "items", "metric": "valor", "aggregation": "sum"},
        {"operation": "aggregate", "dataset": "items", "metric": "valor", "aggregation": "avg"},
        {"operation": "aggregate", "dataset": "items", "group_by": "produto", "metric": "quantidade", "aggregation": "sum", "sort": "quantidade", "sort_direction": "desc", "limit": 5},
        {"operation": "aggregate", "dataset": "items", "metric": "valor", "aggregation": "sum", "periodo": "2024"},
    ],
)
def test_gpt_oss_fake_plans_validate_as_data_query(plan):
    assert DataQuery.model_validate(plan).dataset == "items"


@pytest.mark.parametrize(
    "plan",
    [
        {"operation": "invalid", "dataset": "items"},
        {"operation": "aggregate", "dataset": "items"},
        {"operation": "list", "dataset": "items", "sort_direction": "desc"},
    ],
)
def test_gpt_oss_invalid_fake_plans_are_rejected(plan):
    with pytest.raises(ValueError):
        DataQuery.model_validate(plan)


def test_text_that_mentions_rate_limit_without_http_status_is_not_a_429():
    error = RuntimeError("rate_limit_exceeded; try again in 7s")

    assert QueryService._provider_error(error, "groq") is None


def test_wrapped_gemini_resource_exhausted_triggers_fallback_classification():
    error = RuntimeError(
        "Error calling model (RESOURCE_EXHAUSTED): 429 RESOURCE_EXHAUSTED. "
        "Quota exceeded. Please retry in 45.469s."
    )

    classified = QueryService._provider_error(error, "gemini")

    assert classified.metadata["provider_rate_limit_source"] == "gemini"
    assert classified.retry_after_seconds == 46
    assert classified.code == "provider_quota_exhausted"


def test_real_http_429_is_labeled_as_provider_source():
    class RateLimitError(RuntimeError):
        status_code = 429
        headers = {"retry-after": "7.66s"}

    error = QueryService._provider_error(RateLimitError("rate limit"), "groq")

    assert error.metadata["provider_rate_limit_source"] == "groq"
    assert error.retry_after_seconds == 8


def test_aggregate_sort_alias_is_normalized_without_another_generation():
    response = {
        "parsed": {
            "operation": "aggregate",
            "dataset": "items",
            "metric": "quantidade",
            "aggregation": "sum",
            "sort": "sum",
            "sort_direction": "desc",
            "limit": 1,
        }
    }

    assert QueryService._structured_plan(response).sort == "quantidade"


def test_supplier_plan_prefers_readable_name_over_tax_identifier():
    plan = DataQuery(
        operation="aggregate",
        dataset="items",
        group_by="cpf_cnpj_emitente",
        metric="valor_total",
        aggregation="sum",
        sort="valor_total",
        sort_direction="desc",
        limit=1,
    )
    manager = SimpleNamespace(
        datasets={
            "items": pd.DataFrame(
                columns=["cpf_cnpj_emitente", "razao_social_emitente", "valor_total"]
            )
        }
    )

    normalized = QueryService._normalize_plan(
        plan, "Qual fornecedor recebeu o maior valor?", manager
    )

    assert normalized.group_by == "razao_social_emitente"


def test_product_plan_prefers_description_over_numeric_identifier():
    plan = DataQuery(
        operation="aggregate",
        dataset="items",
        group_by="numero_produto",
        metric="quantidade",
        aggregation="sum",
        sort="quantidade",
        sort_direction="desc",
        limit=1,
    )
    manager = SimpleNamespace(
        datasets={
            "items": pd.DataFrame(
                columns=["numero_produto", "descricao_do_produto_servico", "quantidade"]
            )
        }
    )

    normalized = QueryService._normalize_plan(
        plan, "Qual produto apresentou o maior volume comprado?", manager
    )

    assert normalized.group_by == "descricao_do_produto_servico"


@pytest.mark.parametrize(
    ("aggregation", "direction"),
    [("max", "desc"), ("min", "asc")],
)
def test_extreme_value_question_returns_the_complete_record(aggregation, direction):
    plan = DataQuery(
        operation="aggregate",
        dataset="items",
        metric="valor_total",
        aggregation=aggregation,
    )
    manager = SimpleNamespace(
        datasets={"items": pd.DataFrame(columns=["produto", "valor_total"])}
    )

    normalized = QueryService._normalize_plan(
        plan,
        f"Qual é o {aggregation} valor_total e qual registro possui esse valor?",
        manager,
    )

    assert normalized == DataQuery(
        operation="list",
        dataset="items",
        sort="valor_total",
        sort_direction=direction,
        limit=1,
    )


@pytest.mark.parametrize(
    "question",
    [
        "Qual foi o total gasto no período?",
        "Qual foi o total gasto?",
        "Quanto foi gasto?",
        "Qual o valor total comprado?",
        "Quanto gastamos no mês?",
        "Quanto gastamos em 2024?",
    ],
)
def test_total_spend_phrasings_accept_a_structurally_valid_fake_plan(question):
    response = {
        "parsed": {
            "operation": "aggregate",
            "dataset": "items",
            "metric": "valor_total",
            "aggregation": "sum",
            "periodo": None,
        }
    }

    assert question
    assert QueryService._structured_plan(response).operation == "aggregate"


def test_local_budget_block_is_distinct_and_does_not_call_provider(tmp_path, caplog):
    health = ProviderHealth()
    health.update_budget("groq", "openai/gpt-oss-20b", remaining_tokens=0)
    service = QueryService(SessionRegistry(str(tmp_path)), provider_health=health)

    with caplog.at_level("INFO"), pytest.raises(Exception):
        service._ensure_provider_available("groq", 1, "query-local-budget")

    log = " ".join(caplog.messages)
    assert "decision=LOCAL_TOKEN_BUDGET_BLOCK" in log
    assert "provider_called=false" in log
    assert "provider_rate_limit_source=local_budget" in log


@pytest.mark.parametrize(
    ("open_circuit", "decision", "source"),
    [
        (True, "LOCAL_CIRCUIT_OPEN", "circuit_breaker"),
        (False, "LOCAL_COOLDOWN", "cooldown"),
    ],
)
def test_local_circuit_and_cooldown_have_distinct_decisions(
    tmp_path, caplog, open_circuit, decision, source
):
    health = ProviderHealth()
    health.cooldown(
        "groq", 10, "openai/gpt-oss-20b", open_circuit=open_circuit
    )
    service = QueryService(SessionRegistry(str(tmp_path)), provider_health=health)

    with caplog.at_level("INFO"), pytest.raises(Exception):
        service._ensure_provider_available("groq", 1, "query-local-state")

    log = " ".join(caplog.messages)
    assert f"decision={decision}" in log
    assert f"provider_rate_limit_source={source}" in log
    assert "provider_called=false" in log
