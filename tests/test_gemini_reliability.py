from types import SimpleNamespace

import pandas as pd
import pytest

import services.query_service as query_service
from agents.csv_agent import build_tools
from services.exceptions import ProviderQuotaExhaustedError, ProviderRateLimitError
from services.gemini_errors import parse_gemini_error
from services.provider_health import ProviderHealth
from services.query_service import QueryService
from services.session_registry import SessionRegistry


class GeminiError(RuntimeError):
    code = 429

    def __init__(self, details):
        self.details = details
        self.status = details.get("error", {}).get("status")
        super().__init__("Gemini request failed")


def quota_error(quota_id=None, metric="generativelanguage.googleapis.com/generate_content_free_tier_requests", retry="7.2s"):
    details = []
    if quota_id:
        details.append(
            {
                "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                "violations": [
                    {
                        "quotaMetric": metric,
                        "quotaId": quota_id,
                        "quotaDimensions": {"model": "gemini-flash-latest", "location": "global"},
                        "quotaValue": "10",
                    }
                ],
            }
        )
    if retry:
        details.append(
            {
                "@type": "type.googleapis.com/google.rpc.RetryInfo",
                "retryDelay": retry,
            }
        )
    return GeminiError(
        {
            "error": {
                "code": 429,
                "status": "RESOURCE_EXHAUSTED",
                "message": "Quota exceeded; check plan and billing details",
                "details": details,
            }
        }
    )


def configured_registry(tmp_path):
    registry = SessionRegistry(str(tmp_path))
    session = registry.create()
    session.manager.datasets = {
        "items": pd.DataFrame(
            {
                "produto": ["A", "B", "A"],
                "fornecedor": ["F1", "F2", "F1"],
                "quantidade": [2, 5, 3],
                "valor": [10.0, 30.0, 20.0],
                "periodo": ["2024", "2024", "2023"],
            }
        )
    }
    session.manager.dictionary = {
        "items": {
            "columns": ["produto", "fornecedor", "quantidade", "valor", "periodo"],
            "dtypes": {
                "produto": "object",
                "fornecedor": "object",
                "quantidade": "int64",
                "valor": "float64",
                "periodo": "object",
            },
            "descriptions": {},
        }
    }
    registry.register(session)
    return registry, session


def raw_response(**usage):
    return SimpleNamespace(
        usage_metadata=usage or {"input_tokens": 40, "output_tokens": 12, "total_tokens": 52},
        response_metadata={},
        tool_calls=[],
    )


@pytest.mark.parametrize(
    "plan",
    [
        {"operation": "count", "dataset": "items"},
        {"operation": "aggregate", "dataset": "items", "metric": "valor", "aggregation": "sum"},
        {"operation": "aggregate", "dataset": "items", "metric": "valor", "aggregation": "avg"},
        {
            "operation": "aggregate",
            "dataset": "items",
            "group_by": "produto",
            "metric": "quantidade",
            "aggregation": "sum",
            "sort": "quantidade",
            "sort_direction": "desc",
            "limit": 2,
        },
        {
            "operation": "aggregate",
            "dataset": "items",
            "metric": "valor",
            "aggregation": "sum",
            "periodo": "2024",
        },
        {"operation": "list", "dataset": "items", "sort": "valor", "sort_direction": "desc", "limit": 1},
    ],
)
def test_gemini_structured_plans_execute_with_one_generation(monkeypatch, tmp_path, plan):
    registry, session = configured_registry(tmp_path)
    calls = []
    agent = SimpleNamespace(
        invoke=lambda messages: (
            calls.append(messages)
            or {"raw": raw_response(), "parsed": plan, "parsing_error": None}
        )
    )
    monkeypatch.setattr(query_service, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "create_agent", lambda manager, tools, provider=None: agent)

    result = QueryService(registry).query(session.dataset_id, "consulta válida")

    assert result.data is not None
    assert result.telemetry["gemini_calls"] == 1
    assert result.telemetry["provider_calls"] == 1
    assert result.telemetry["tools_called"] == ["query_data"]
    assert len(calls) == 1


def test_gemini_tools_do_not_include_describe_data(tmp_path):
    registry, session = configured_registry(tmp_path)

    assert [tool.name for tool in build_tools(session.manager, provider="gemini")] == ["query_data"]


@pytest.mark.parametrize(
    ("quota_id", "metric", "diagnosis", "exception_type"),
    [
        ("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "generate_content_requests", "GEMINI_RATE_LIMIT_RPM", ProviderRateLimitError),
        ("GenerateContentInputTokensPerModelPerMinute-FreeTier", "generate_content_input_token_count", "GEMINI_RATE_LIMIT_TPM", ProviderRateLimitError),
        ("GenerateRequestsPerDayPerProjectPerModel-FreeTier", "generate_content_requests", "GEMINI_QUOTA_RPD", ProviderQuotaExhaustedError),
        ("ProjectSpendLimit", "billing.googleapis.com/spend", "GEMINI_SPEND_LIMIT", ProviderQuotaExhaustedError),
    ],
)
def test_gemini_quota_failure_is_classified_structurally(quota_id, metric, diagnosis, exception_type):
    error = quota_error(quota_id, metric)

    parsed = parse_gemini_error(error)
    classified = QueryService._provider_error(error, "gemini")

    assert parsed["diagnosis"] == diagnosis
    assert parsed["quota_id"] == quota_id
    assert parsed["quota_dimensions"]["model"] == "gemini-flash-latest"
    assert isinstance(classified, exception_type)
    assert classified.retry_after_seconds == 8
    assert classified.metadata["quota_value"] == "10"


def test_gemini_generic_resource_exhausted_remains_explicitly_unknown():
    classified = QueryService._provider_error(quota_error(retry="1m"), "gemini")

    assert isinstance(classified, ProviderQuotaExhaustedError)
    assert classified.metadata["diagnosis"] == "GEMINI_RESOURCE_EXHAUSTED_UNKNOWN"
    assert classified.retry_after_seconds == 60


def test_langchain_wrapped_gemini_error_preserves_structured_quota_details():
    cause = quota_error("GenerateContentInputTokensPerModelPerMinute-FreeTier")
    try:
        raise RuntimeError("Error calling model (RESOURCE_EXHAUSTED)") from cause
    except RuntimeError as wrapped:
        classified = QueryService._provider_error(wrapped, "gemini")

    assert classified.metadata["diagnosis"] == "GEMINI_RATE_LIMIT_TPM"
    assert classified.metadata["quota_id"] == "GenerateContentInputTokensPerModelPerMinute-FreeTier"
    assert classified.retry_after_seconds == 8


@pytest.mark.parametrize("raw, expected", [("7s", 7), ("45.2s", 46), ("1m", 60)])
def test_gemini_retry_info_is_never_rounded_down(raw, expected):
    classified = QueryService._provider_error(quota_error(retry=raw), "gemini")

    assert classified.retry_after_seconds == expected


def test_five_consecutive_gemini_queries_make_exactly_five_generations(monkeypatch, tmp_path):
    registry, session = configured_registry(tmp_path)
    calls = []

    class Agent:
        def invoke(self, messages):
            calls.append(messages)
            return {
                "raw": raw_response(),
                "parsed": {"operation": "count", "dataset": "items"},
                "parsing_error": None,
            }

    agent = Agent()
    monkeypatch.setattr(query_service, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "create_agent", lambda manager, tools, provider=None: agent)
    service = QueryService(registry)

    results = [service.query(session.dataset_id, f"Q{index}") for index in range(1, 6)]

    assert len(calls) == 5
    assert all(result.telemetry["gemini_calls"] == 1 for result in results)
    assert all(result.telemetry["provider_calls"] == 1 for result in results)
    assert all(result.telemetry["fallback_count"] == 0 for result in results)


@pytest.mark.parametrize(
    "response",
    [
        {"raw": raw_response(), "parsed": None, "parsing_error": ValueError("invalid schema")},
        {
            "raw": raw_response(),
            "parsed": {
                "operation": "aggregate",
                "dataset": "items",
                "metric": "campo_inexistente",
                "aggregation": "sum",
            },
            "parsing_error": None,
        },
    ],
)
def test_invalid_gemini_plan_fails_without_a_repair_generation(monkeypatch, tmp_path, response):
    registry, session = configured_registry(tmp_path)
    calls = []
    monkeypatch.setattr(query_service, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(query_service, "GROQ_API_KEY", None)
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(
        query_service,
        "create_agent",
        lambda manager, tools, provider=None: SimpleNamespace(
            invoke=lambda messages: calls.append(messages) or response
        ),
    )

    with pytest.raises(Exception):
        QueryService(registry).query(session.dataset_id, "consulta inválida")

    assert len(calls) == 1


def test_gemini_429_falls_back_once_without_returning_to_primary(monkeypatch, tmp_path):
    registry, session = configured_registry(tmp_path)
    provider_calls = []

    def create_agent(manager, tools, provider=None):
        selected = provider or "gemini"
        provider_calls.append(selected)
        if selected == "gemini":
            return SimpleNamespace(
                invoke=lambda messages: (_ for _ in ()).throw(
                    quota_error("GenerateRequestsPerMinutePerProjectPerModel-FreeTier")
                )
            )
        return SimpleNamespace(
            invoke=lambda messages: {
                "raw": raw_response(),
                "parsed": {"operation": "count", "dataset": "items"},
                "parsing_error": None,
            }
        )

    monkeypatch.setattr(query_service, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(query_service, "GROQ_API_KEY", "groq-test-key")
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(query_service, "create_agent", create_agent)

    result = QueryService(registry).query(session.dataset_id, "quantos itens?")

    assert provider_calls == ["gemini", "groq"]
    assert result.telemetry["gemini_calls"] == 1
    assert result.telemetry["groq_calls"] == 1
    assert result.telemetry["fallback_count"] == 1
    assert result.telemetry["calls"][0]["diagnosis"] == "GEMINI_RATE_LIMIT_RPM"


@pytest.mark.parametrize(
    "failure",
    [
        quota_error("GenerateRequestsPerMinutePerProjectPerModel-FreeTier"),
        type("Unavailable", (RuntimeError,), {"status_code": 503})("unavailable"),
        TimeoutError("timeout"),
        RuntimeError("network failure"),
        type("BadRequest", (RuntimeError,), {"status_code": 400})("bad request"),
        type("Forbidden", (RuntimeError,), {"status_code": 403})("forbidden"),
    ],
)
def test_gemini_failures_are_not_retried_by_query_service(monkeypatch, tmp_path, failure):
    registry, session = configured_registry(tmp_path)
    calls = []

    def invoke(messages):
        calls.append(messages)
        raise failure

    monkeypatch.setattr(query_service, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(query_service, "GROQ_API_KEY", None)
    monkeypatch.setattr(query_service, "is_ai_configured", lambda: True)
    monkeypatch.setattr(
        query_service,
        "create_agent",
        lambda manager, tools, provider=None: SimpleNamespace(invoke=invoke),
    )

    with pytest.raises(Exception):
        QueryService(registry).query(session.dataset_id, "consulta")

    assert len(calls) == 1


def test_usage_includes_gemini_thought_cache_and_tool_tokens():
    response = raw_response(
        input_tokens=100,
        output_tokens=20,
        total_tokens=125,
        input_token_details={"cache_read": 30},
        output_token_details={"reasoning": 5},
        tool_use_prompt_token_count=2,
    )

    assert QueryService._usage(response) == {
        "input_tokens": 100,
        "output_tokens": 20,
        "thought_tokens": 5,
        "cached_tokens": 30,
        "tool_use_tokens": 2,
        "total_tokens": 125,
    }


def test_truncated_structured_output_has_an_explicit_diagnosis():
    response = {
        "raw": SimpleNamespace(response_metadata={"finish_reason": "MAX_TOKENS"}),
        "parsed": None,
        "parsing_error": ValueError("incomplete json"),
    }

    with pytest.raises(Exception, match="truncou.*output tokens"):
        QueryService._structured_plan(response)


def test_gemini_health_is_scoped_by_model():
    health = ProviderHealth()
    health.cooldown("gemini", 30, "gemini-flash-latest", open_circuit=False)

    assert health.remaining("gemini", "gemini-flash-latest") > 0
    assert health.remaining("gemini", "gemini-2.5-flash") == 0
