from fastapi import APIRouter, Depends

from app.config import get_settings
from app.deps import get_current_user
from app.models import User
from app.schemas import SystemStatus

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status", response_model=SystemStatus)
def system_status(_user: User = Depends(get_current_user)) -> SystemStatus:
    settings = get_settings()
    model_configured = bool(settings.llm_api_key.get_secret_value().strip())
    return SystemStatus(
        obito_status="online",
        active_model=(
            f"Configured: {settings.llm_model}" if model_configured else "Not configured: hosted LLM"
        ),
        voice_status="Available: push-to-talk in Chat",
        pc_connection="Disconnected (Phase 6)",
        roblox_connection="Disconnected (Phase 7)",
        active_tasks=[],
        notes=[
            "Chat uses a hosted LLM configured on the backend.",
            "Chat messages and recent conversation history are sent to that provider.",
            "The API key stays on the backend and is never sent to the browser.",
            "The assistant has no tools to control your computer or perform external actions.",
            "Voice transcription runs only after a button press and is provided by your browser.",
            "Agents, PC control, and Roblox integrations are not built yet.",
            "This status is real. Features that are not ready are marked clearly.",
        ],
    )
