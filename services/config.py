from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def _env_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


MAX_UPLOAD_BYTES = _env_int("MAX_UPLOAD_BYTES", 500 * 1024 * 1024)
MAX_ZIP_MEMBERS = _env_int("MAX_ZIP_MEMBERS", 1000)
MAX_ZIP_MEMBER_BYTES = _env_int("MAX_ZIP_MEMBER_BYTES", 500 * 1024 * 1024)
MAX_ZIP_UNCOMPRESSED_BYTES = _env_int(
    "MAX_ZIP_UNCOMPRESSED_BYTES", 1024 * 1024 * 1024
)


def is_ai_configured() -> bool:
    return bool(GOOGLE_API_KEY)
