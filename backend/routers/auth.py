from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models
from backend.schemas import (
    SignupRequest,
    LoginRequest,
    ForgotPasswordRequest,
    UserResponse,
    ResetPasswordRequest
)
from backend.auth import hash_password, verify_password, create_access_token
import logging
from backend.config import settings
from backend.dependencies import get_current_user
import secrets
from datetime import datetime, timedelta, timezone
import hashlib
from backend.tests.test_crud import user

router = APIRouter()
logger = logging.getLogger(__name__)


def _set_auth_cookie(response: JSONResponse, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
        max_age=60 * 60 * 24
    )

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
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
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    response = JSONResponse(content={"message": "Account created", 
                                     "user": UserResponse.model_validate(user).model_dump()},
                            status_code=status.HTTP_201_CREATED)
    _set_auth_cookie(response, token)
    
    return response

@router.post("/login", status_code=status.HTTP_200_OK)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid email or password"      
  )
    
    token = create_access_token({"sub": str(user.id)})
    response = JSONResponse(content={"message": "Login successful", 
                                     "user": UserResponse.model_validate(user).model_dump()},
                            status_code=status.HTTP_200_OK)
    _set_auth_cookie(response, token)
    return response

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
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
        logger.info("Password reset link: http://localhost:3000/reset-password?token=%s", token)
    return {"message": "If an account with that email exists, a password reset link has been sent."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_token = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == hash_token(body.token)
    ).first()

    now = datetime.now(timezone.utc).replace(tzinfo=None)  
    if not reset_token or reset_token.expires_at < now:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.id == reset_token.user_id).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.hashed_password = hash_password(body.new_password)
    user.password_changed_at = now 
    db.query(models.PasswordResetToken).filter_by(user_id=user.id).delete()
    db.commit()

    return {"message": "Password has been reset successfully"}

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout():
    response = JSONResponse(content={"message": "Logged out"}, status_code=status.HTTP_200_OK)
    response.delete_cookie(key="access_token", httponly=True, secure=settings.secure_cookie, samesite="lax")
    return response

@router.get("/me", response_model=UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user