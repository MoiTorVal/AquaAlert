from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models
from backend.schemas import (
    SignupRequest,
    LoginRequest,
    ForgotPasswordRequest,
    UserResponse,
    UserUpdateRequest,
    ResetPasswordRequest
)
from backend.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    hash_password,
    verify_password,
)
from fastapi import Cookie
from backend.rate_limit import AUTH_WRITE_LIMIT, limiter
import logging
from backend.config import settings
from backend.dependencies import get_current_user
import secrets
from datetime import datetime, timedelta, timezone
import hashlib


router = APIRouter()
logger = logging.getLogger(__name__)


def _set_auth_cookie(response: JSONResponse, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
        # Match the JWT lifetime so the cookie can't outlive the token.
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _set_refresh_cookie(response: JSONResponse, token: str):
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
        # Only auth endpoints ever need this cookie — scoping the path keeps
        # it off every other request.
        path="/auth",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _issue_refresh_token(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    db.add(models.RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()
    return token


def _revoke_all_refresh_tokens(db: Session, user_id: int) -> None:
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user_id,
        models.RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": datetime.now(timezone.utc)})


def _start_session(db: Session, response: JSONResponse, user_id: int) -> JSONResponse:
    _set_auth_cookie(response, create_access_token({"sub": str(user_id)}))
    _set_refresh_cookie(response, _issue_refresh_token(db, user_id))
    return response

@router.post("/signup", status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_WRITE_LIMIT)
def signup(request: Request, body: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = models.User(
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two concurrent signups can both pass the check above; the unique
        # constraint on email is the real guard.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    db.refresh(user)

    response = JSONResponse(content={"message": "Account created",
                                     "user": UserResponse.model_validate(user).model_dump()},
                            status_code=status.HTTP_201_CREATED)
    return _start_session(db, response, user.id)

@router.post("/login", status_code=status.HTTP_200_OK)
@limiter.limit(AUTH_WRITE_LIMIT)
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


    response = JSONResponse(content={"message": "Login successful",
                                     "user": UserResponse.model_validate(user).model_dump()},
                            status_code=status.HTTP_200_OK)
    return _start_session(db, response, user.id)

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit(AUTH_WRITE_LIMIT)
def forgot_password(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if user:
        db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.user_id == user.id
        ).delete()
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        reset_token = models.PasswordResetToken(
            user_id=user.id,
            token=hash_token(token),
            expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()
        if settings.log_reset_links:
            # Dev-only stand-in until email delivery (SendGrid) ships — a live
            # credential must never reach production logs.
            logger.info(
                "Password reset link: %s/reset-password?token=%s",
                settings.frontend_base_url, token,
            )
    return {"message": "If an account with that email exists, a password reset link has been sent."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit(AUTH_WRITE_LIMIT)
def reset_password(request: Request, body: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_token = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == hash_token(body.token)
    ).first()

    now = datetime.now(timezone.utc)
    if not reset_token or reset_token.expires_at < now:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.id == reset_token.user_id).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.hashed_password = hash_password(body.new_password)
    user.password_changed_at = now
    db.query(models.PasswordResetToken).filter_by(user_id=user.id).delete()
    # Kill every open session: password_changed_at invalidates outstanding
    # access tokens (iat check), this revokes the refresh tokens.
    _revoke_all_refresh_tokens(db, user.id)
    db.commit()

    return {"message": "Password has been reset successfully"}


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh(
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    if refresh_token is None:
        raise credentials_exception

    row = db.query(models.RefreshToken).filter(
        models.RefreshToken.token_hash == hash_token(refresh_token)
    ).first()
    if row is None:
        raise credentials_exception

    if row.revoked_at is not None:
        # Rotation means a token is only ever presented once. Seeing it again
        # means it was stolen (or replayed) — burn every session for the user.
        _revoke_all_refresh_tokens(db, row.user_id)
        db.commit()
        logger.warning("Revoked refresh token reused for user_id=%s — all sessions revoked", row.user_id)
        raise credentials_exception

    if row.expires_at < datetime.now(timezone.utc):
        raise credentials_exception

    row.revoked_at = datetime.now(timezone.utc)
    db.commit()

    response = JSONResponse(content={"message": "Token refreshed"}, status_code=status.HTTP_200_OK)
    return _start_session(db, response, row.user_id)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token is not None:
        db.query(models.RefreshToken).filter(
            models.RefreshToken.token_hash == hash_token(refresh_token),
            models.RefreshToken.revoked_at.is_(None),
        ).update({"revoked_at": datetime.now(timezone.utc)})
        db.commit()
    response = JSONResponse(content={"message": "Logged out"}, status_code=status.HTTP_200_OK)
    response.delete_cookie(key="access_token", httponly=True, secure=settings.secure_cookie, samesite="lax")
    response.delete_cookie(key="refresh_token", path="/auth", httponly=True, secure=settings.secure_cookie, samesite="lax")
    return response

@router.get("/me", response_model=UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # exclude_unset so omitted fields stay untouched while an explicit null
    # clears an equity answer (voluntary self-ID, must be revocable)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user