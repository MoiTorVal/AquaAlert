from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from backend.config import settings

SECRET_KEY = settings.secret_key.get_secret_value()

ALGORITHM = "HS256"
# Access tokens are short-lived and never revoked individually — the
# refresh_tokens table is the revocable session record. A leaked access
# token is only good for this window.
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 1

class TokenExpiredError(Exception):
    pass
class InvalidTokenError(Exception):
    pass

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    # iat lets get_current_user reject tokens issued before a password reset
    to_encode["iat"] = now
    to_encode["exp"] = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenError("Invalid token")