from services.config import GOOGLE_API_KEY, is_ai_configured


def test_gemini_configuration_is_optional_for_backend_tests():
    assert is_ai_configured() is bool(GOOGLE_API_KEY)
