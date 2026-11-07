from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import ProfileUpdateRequest, UserPublic
from app.services import log_activity

router = APIRouter(prefix="/api/users", tags=["users"])


@router.patch("/me", response_model=UserPublic)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    updated_name = (payload.display_name or payload.username or user.display_name).strip()
    user.display_name = updated_name
    db.commit()
    db.refresh(user)
    log_activity(db, user, "profile_updated", "Display name updated.")
    return user
