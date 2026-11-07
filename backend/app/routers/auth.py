from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user
from app.models import SessionToken, User
from app.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    UserPublic,
)
from app.security import (
    hash_secret,
    hash_token,
    new_recovery_code,
    new_session_token,
    normalize_recovery_code,
    session_expiry,
    verify_secret,
)
from app.services import log_activity

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.session_days * 24 * 60 * 60,
        path="/",
    )


def _create_session(db: Session, user: User, response: Response) -> None:
    raw = new_session_token()
    db.add(SessionToken(user_id=user.id, token_hash=hash_token(raw), expires_at=session_expiry()))
    db.commit()
    _set_session_cookie(response, raw)


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    recovery_code = new_recovery_code()
    display_name = payload.display_name or payload.username or "User"
    user = User(
        email=email,
        display_name=display_name.strip(),
        password_hash=hash_secret(payload.password),
        recovery_code_hash=hash_secret(normalize_recovery_code(recovery_code)),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _create_session(db, user, response)
    log_activity(db, user, "account_created", "New OBITO account created.")
    return AuthResponse(user=UserPublic.model_validate(user), recovery_code=recovery_code)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_secret(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect.")

    _create_session(db, user, response)
    log_activity(db, user, "signed_in", "Signed in to OBITO.")
    return AuthResponse(user=UserPublic.model_validate(user))


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    settings = get_settings()
    log_activity(db, user, "signed_out", "Signed out of OBITO.")
    db.query(SessionToken).filter(SessionToken.user_id == user.id).delete()
    db.commit()
    response.delete_cookie(settings.cookie_name, path="/")
    return {"ok": "signed_out"}


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    if not verify_secret(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )

    if payload.confirm_password is not None and payload.confirm_password != payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    user.password_hash = hash_secret(payload.new_password)
    db.query(SessionToken).filter(SessionToken.user_id == user.id).delete()
    db.commit()
    log_activity(db, user, "password_changed", "Password was changed from the account settings screen.")
    return {"ok": "password_updated"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    email = payload.email.lower().strip()
    if payload.confirm_password is not None and payload.confirm_password != payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_secret(normalize_recovery_code(payload.recovery_code), user.recovery_code_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or recovery code is incorrect.",
        )

    user.password_hash = hash_secret(payload.new_password)
    db.query(SessionToken).filter(SessionToken.user_id == user.id).delete()
    db.commit()
    log_activity(db, user, "password_reset", "Password was reset with recovery code.")
    return {"ok": "password_updated"}
