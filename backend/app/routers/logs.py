from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import ActivityLog, User
from app.schemas import ActivityLogPublic

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=list[ActivityLogPublic])
def list_logs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ActivityLog]:
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(100)
        .all()
    )
