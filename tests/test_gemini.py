import services.config as config
from services.config import GOOGLE_API_KEY, is_ai_configured


def test_gemini_configuration_is_optional_for_backend_tests():
    assert is_ai_configured() is bool(GOOGLE_API_KEY)


def test_configuration_error_explains_missing_selected_provider_key(monkeypatch):
    monkeypatch.setattr(config, "AI_PROVIDER", "groq")
    monkeypatch.setattr(config, "GROQ_API_KEY", None)

    assert config.ai_configuration_error() == (
        "GROQ_API_KEY não foi configurada para o provider Groq."
    )


def test_configuration_error_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(config, "AI_PROVIDER", "unknown")

    assert config.ai_configuration_error() == (
        "AI_PROVIDER deve ser 'gemini' ou 'groq'."
    )
