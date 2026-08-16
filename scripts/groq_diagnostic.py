"""Run exactly one minimal Groq request without the agent or local rate budget."""

import json
import os
import sys

import httpx
from dotenv import load_dotenv


RATE_HEADERS = (
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-tokens",
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "retry-after",
)


def main() -> int:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_DIAGNOSTIC_MODEL", "openai/gpt-oss-20b")
    if not api_key:
        print(json.dumps({"status": "not_run", "reason": "GROQ_API_KEY ausente"}))
        return 2

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Responda apenas OK."}],
        "temperature": 0,
        "reasoning_effort": "low",
        "include_reasoning": False,
        "max_completion_tokens": 32,
    }
    try:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=60,
        )
    except httpx.HTTPError as error:
        print(json.dumps({"status": "transport_error", "error": type(error).__name__}))
        return 1

    try:
        body = response.json()
    except ValueError:
        body = {}
    usage = body.get("usage", {}) if isinstance(body, dict) else {}
    result = {
        "http_status": response.status_code,
        "model": body.get("model", model) if isinstance(body, dict) else model,
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "headers": {name: response.headers.get(name) for name in RATE_HEADERS},
    }
    if response.status_code >= 400:
        error = body.get("error", {}) if isinstance(body, dict) else {}
        result["error_type"] = error.get("type")
        result["error_code"] = error.get("code")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if response.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
