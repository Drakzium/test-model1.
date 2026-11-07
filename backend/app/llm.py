import json
from typing import TypedDict
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.config import get_settings

SYSTEM_PROMPT = (
    "You are OBITO, a helpful personal AI assistant. Answer clearly, accurately, and naturally. "
    "You can discuss ideas and provide instructions, but this application does not give you tools "
    "to control the user's computer, access their files, or perform external actions. Never claim "
    "that you performed an action. Ask clarifying questions when they would improve your answer."
)


class ChatCompletionMessage(TypedDict):
    role: str
    content: str


def generate_reply(messages: list[ChatCompletionMessage]) -> str:
    settings = get_settings()
    api_key = settings.llm_api_key.get_secret_value().strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hosted AI is not configured. Add LLM_API_KEY to backend/.env and restart the backend.",
        )

    base_url = settings.llm_base_url.rstrip("/")
    if urlparse(base_url).scheme != "https":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM_BASE_URL must use HTTPS to protect your API key.",
        )

    payload = {
        "model": settings.llm_model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
    }
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.llm_timeout_seconds) as response:
            response_body = response.read()
    except HTTPError as error:
        if error.code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The hosted AI rejected the configured credentials. Check LLM_API_KEY.",
            ) from error
        if error.code == 429:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The hosted AI is rate-limiting requests. Please try again shortly.",
            ) from error
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The hosted AI returned HTTP {error.code}. Please try again later.",
        ) from error
    except TimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The hosted AI took too long to respond. Please try again.",
        ) from error
    except URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="The hosted AI took too long to respond. Please try again.",
            ) from error
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach the hosted AI. Check the backend's internet connection and LLM_BASE_URL.",
        ) from error

    try:
        result = json.loads(response_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The hosted AI returned an invalid response.",
        ) from error

    choices = result.get("choices") if isinstance(result, dict) else None
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The hosted AI returned no answer.",
        )
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The hosted AI returned no text answer.",
        )
    return content.strip()
