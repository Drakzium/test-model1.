from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import SessionToken, User
from app.security import hash_token


def get_current_user(
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=get_settings().cookie_name),
) -> User:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in.")

    token_hash = hash_token(session_token)
    record = db.query(SessionToken).filter(SessionToken.token_hash == token_hash).first()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires = record.expires_at.replace(tzinfo=None) if record and record.expires_at.tzinfo else (record.expires_at if record else None)
    if record is None or expires is None or expires < now:
        if record is not None:
            db.delete(record)
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please sign in again.")

    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in.")
    return user
