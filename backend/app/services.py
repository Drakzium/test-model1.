from sqlalchemy.orm import Session

from app.models import ActivityLog, User


def log_activity(db: Session, user: User, action: str, detail: str = "") -> None:
    db.add(ActivityLog(user_id=user.id, action=action, detail=detail[:500]))
    db.commit()
