from fastapi import APIRouter

from services.config import is_ai_configured

router = APIRouter()


@router.get("/api/health")
def health() -> dict[str, bool | str]:
    return {"status": "ok", "aiConfigured": is_ai_configured()}
