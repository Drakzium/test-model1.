from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user
from app.llm import ChatCompletionMessage, generate_reply
from app.models import ChatConversation, ChatMessage, User
from app.schemas import (
    ChatConversationPublic,
    ChatModelStatus,
    ChatMessagePublic,
    ChatMessageRequest,
    ChatTurnPublic,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])
MAX_CONTEXT_MESSAGES = 20


@router.get("/model", response_model=ChatModelStatus)
def model_status(_user: User = Depends(get_current_user)) -> ChatModelStatus:
    settings = get_settings()
    return ChatModelStatus(
        provider="OpenAI-compatible hosted API",
        model=settings.llm_model,
        configured=bool(settings.llm_api_key.get_secret_value().strip()),
    )


def _owned_conversation(db: Session, user: User, conversation_id: int) -> ChatConversation:
    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == user.id,
        )
        .first()
    )
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return conversation


@router.get("/conversations", response_model=list[ChatConversationPublic])
def list_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ChatConversation]:
    return (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == user.id)
        .order_by(ChatConversation.updated_at.desc(), ChatConversation.id.desc())
        .limit(100)
        .all()
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessagePublic])
def list_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ChatMessage]:
    conversation = _owned_conversation(db, user, conversation_id)
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.id.asc())
        .limit(200)
        .all()
    )


@router.post("/messages", response_model=ChatTurnPublic)
def send_message(
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatTurnPublic:
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Message cannot be blank.")

    if payload.conversation_id is None:
        title = " ".join(content.split())
        if len(title) > 48:
            title = f"{title[:45].rstrip()}..."
        conversation = ChatConversation(user_id=user.id, title=title)
        db.add(conversation)
        db.flush()
    else:
        conversation = _owned_conversation(db, user, payload.conversation_id)

    previous_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.id.desc())
        .limit(MAX_CONTEXT_MESSAGES)
        .all()
    )
    previous_messages.reverse()
    history: list[ChatCompletionMessage] = [
        {
            "role": "assistant" if message.role == "assistant" else "user",
            "content": message.content,
        }
        for message in previous_messages
    ]
    history.append({"role": "user", "content": content})

    user_message = ChatMessage(conversation_id=conversation.id, role="user", content=content)
    assistant_message = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=generate_reply(history),
    )
    conversation.updated_at = datetime.now(timezone.utc)
    db.add_all([user_message, assistant_message])
    db.commit()
    db.refresh(conversation)
    db.refresh(user_message)
    db.refresh(assistant_message)

    return ChatTurnPublic(
        conversation=ChatConversationPublic.model_validate(conversation),
        messages=[
            ChatMessagePublic.model_validate(user_message),
            ChatMessagePublic.model_validate(assistant_message),
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    conversation = _owned_conversation(db, user, conversation_id)
    db.delete(conversation)
    db.commit()
