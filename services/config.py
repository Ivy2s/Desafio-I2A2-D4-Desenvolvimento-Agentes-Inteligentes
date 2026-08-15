from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY_ALT = os.getenv("GOOGLE_API_KEY_ALT")
GEMINI_PROFILE = os.getenv("GEMINI_PROFILE", "primary").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODEL_ALT = os.getenv("GEMINI_MODEL_ALT", "gemini-3.5-flash")


def _env_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


MAX_UPLOAD_BYTES = _env_int("MAX_UPLOAD_BYTES", 500 * 1024 * 1024)
MAX_ZIP_MEMBERS = _env_int("MAX_ZIP_MEMBERS", 1000)
MAX_ZIP_MEMBER_BYTES = _env_int("MAX_ZIP_MEMBER_BYTES", 500 * 1024 * 1024)
MAX_ZIP_UNCOMPRESSED_BYTES = _env_int(
    "MAX_ZIP_UNCOMPRESSED_BYTES", 1024 * 1024 * 1024
)
MAX_AGENT_ITERATIONS = _env_int("MAX_AGENT_ITERATIONS", 5)
AGENT_REQUEST_TIMEOUT_SECONDS = _env_float("AGENT_REQUEST_TIMEOUT_SECONDS", 60.0)
AGENT_RETRIES = _env_int("AGENT_RETRIES", 2)
MAX_QUERY_RESULT_ROWS = _env_int("MAX_QUERY_RESULT_ROWS", 1000)


def is_ai_configured() -> bool:
    return bool(selected_gemini_credentials()[0])


def selected_gemini_credentials() -> tuple[str | None, str]:
    """Retorna a chave/modelo do perfil sem remover o perfil primário."""
    if GEMINI_PROFILE == "alternative":
        return GOOGLE_API_KEY_ALT or GOOGLE_API_KEY, GEMINI_MODEL_ALT
    return GOOGLE_API_KEY, GEMINI_MODEL
