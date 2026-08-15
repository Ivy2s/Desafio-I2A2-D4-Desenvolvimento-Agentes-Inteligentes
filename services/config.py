from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


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
    return bool(GROQ_API_KEY if AI_PROVIDER == "groq" else GOOGLE_API_KEY)


def selected_ai_credentials() -> tuple[str | None, str]:
    if AI_PROVIDER == "groq":
        return GROQ_API_KEY, GROQ_MODEL
    return GOOGLE_API_KEY, GEMINI_MODEL
