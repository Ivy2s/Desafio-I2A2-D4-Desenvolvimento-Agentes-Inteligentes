from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def is_ai_configured() -> bool:
    return bool(GOOGLE_API_KEY)
