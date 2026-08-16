from typing import Any


def parse_gemini_error(error: Exception) -> dict[str, Any]:
    """Extract Google RPC error details without depending on rendered messages."""
    payload = _payload(error)
    root = payload.get("error", payload) if isinstance(payload, dict) else {}
    details = root.get("details", []) if isinstance(root, dict) else []
    if not isinstance(details, list):
        details = [details]

    result: dict[str, Any] = {
        "http_status": next(
            (
                value
                for current in _error_chain(error)
                if (value := _integer(getattr(current, "code", None))) is not None
            ),
            None,
        )
        or _integer(root.get("code")),
        "status": root.get("status")
        or next(
            (
                getattr(current, "status", None)
                for current in _error_chain(error)
                if getattr(current, "status", None)
            ),
            None,
        ),
    }
    violations: list[dict[str, Any]] = []
    for detail in details:
        if not isinstance(detail, dict):
            continue
        detail_type = str(detail.get("@type") or detail.get("type") or "")
        if detail_type.endswith("RetryInfo"):
            result["retry_delay"] = detail.get("retryDelay") or detail.get("retry_delay")
        if detail_type.endswith("QuotaFailure"):
            raw_violations = detail.get("violations", [])
            if isinstance(raw_violations, dict):
                raw_violations = [raw_violations]
            violations.extend(item for item in raw_violations if isinstance(item, dict))

    if violations:
        violation = violations[0]
        dimensions = violation.get("quotaDimensions") or violation.get("quota_dimensions") or {}
        metric = violation.get("quotaMetric") or violation.get("quota_metric")
        quota_id = violation.get("quotaId") or violation.get("quota_id")
        result.update(
            {
                "quota_metric": metric,
                "quota_id": quota_id,
                "quota_dimensions": dimensions,
                "quota_value": violation.get("quotaValue") or violation.get("quota_value"),
                "model": dimensions.get("model") if isinstance(dimensions, dict) else None,
            }
        )

    diagnosis = _diagnosis(result, root)
    if diagnosis:
        result["diagnosis"] = diagnosis
    return {key: value for key, value in result.items() if value is not None}


def _payload(error: Exception) -> dict[str, Any]:
    for current in _error_chain(error):
        details = getattr(current, "details", None)
        if isinstance(details, dict):
            return details
        response = getattr(current, "response", None)
        if response is not None:
            try:
                value = response.json()
                if isinstance(value, dict):
                    return value
            except (AttributeError, TypeError, ValueError):
                pass
    return {}


def _error_chain(error: Exception):
    seen = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _diagnosis(result: dict[str, Any], root: dict[str, Any]) -> str | None:
    quota_text = " ".join(
        str(value).lower()
        for value in (
            result.get("quota_metric"),
            result.get("quota_id"),
        )
        if value
    )
    if any(
        marker in quota_text
        for marker in (
            "tokensperminute",
            "tokens_per_minute",
            "token per minute",
            "input_token",
            "inputtoken",
        )
    ):
        return "GEMINI_RATE_LIMIT_TPM"
    if any(marker in quota_text for marker in ("requestsperminute", "requests_per_minute", "request per minute", "rpm")):
        return "GEMINI_RATE_LIMIT_RPM"
    if any(marker in quota_text for marker in ("requestsperday", "requests_per_day", "request per day", "perday", "rpd", "daily")):
        return "GEMINI_QUOTA_RPD"
    if any(marker in quota_text for marker in ("spend", "billing", "credit")):
        return "GEMINI_SPEND_LIMIT"
    if not quota_text and any(
        marker in str(root.get("message", "")).lower()
        for marker in ("spend limit", "billing quota", "credit exhausted")
    ):
        return "GEMINI_SPEND_LIMIT"
    status = str(result.get("status", "")).upper()
    if status == "RESOURCE_EXHAUSTED" or result.get("http_status") == 429:
        return "GEMINI_RESOURCE_EXHAUSTED_UNKNOWN"
    return None


def _integer(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
