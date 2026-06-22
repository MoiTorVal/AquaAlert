from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_db_url(url: str) -> str:
    """Pin the SQLAlchemy driver and modernise the scheme.

    Managed Postgres (Railway, Heroku) hands out ``postgres://`` or
    ``postgresql://`` DSNs. SQLAlchemy rejects the bare ``postgres://`` scheme,
    and the rest of the app runs on psycopg2, so coerce both to
    ``postgresql+psycopg2://``. A URL that already names a driver is left as-is.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


class Settings(BaseSettings):
    secret_key: SecretStr
    # Full DSN wins when set (Railway/Heroku expose DATABASE_URL); otherwise the
    # discrete DB_* vars below are required (enforced by _require_db_config).
    # SecretStr keeps the embedded password out of logs and tracebacks.
    database_url: SecretStr | None = None
    db_user: str | None = None
    db_password: SecretStr | None = None
    db_host: str | None = None
    db_name: str | None = None
    db_port: int | None = None
    openet_api_key: SecretStr | None = None
    # Spatial CIMIS key for provisional ET gap-fill; unset = gap-fill off.
    cimis_app_key: SecretStr | None = None
    # Twilio SMS alerts; all four unset = SMS features off.
    twilio_account_sid: str | None = None
    twilio_auth_token: SecretStr | None = None
    twilio_from_number: str | None = None
    # Sentinel NDVI ingest; off by default so hosts without geo libs can boot.
    sentinel_enabled: bool = False
    # Exact public URL Twilio posts inbound SMS to (signature is computed
    # over it, so it must match the Twilio console verbatim).
    sms_webhook_url: str | None = None
    next_public_api_base_url: str
    allowed_origins: list[str] = ["http://localhost:3000"]
    # Used to build links sent (or, in dev, logged) to users.
    frontend_base_url: str = "http://localhost:3000"
    # Dev-only: log password-reset links until email delivery ships. Never
    # enable in production — the token is a live credential.
    log_reset_links: bool = False
    # Fail-safe default: auth cookie is HTTPS-only unless dev explicitly
    # opts out (local HTTP dev sets SECURE_COOKIE=false in .env).
    secure_cookie: bool = True
    # SameSite policy for the auth cookies. A cross-site deploy (API and web on
    # different registrable domains, e.g. *.railway.app + *.vercel.app) needs
    # "none" so the browser sends the cookie on cross-origin requests; browsers
    # reject SameSite=None unless the cookie is also Secure. Local/same-site
    # dev uses "lax".
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    # Opt-in: jobs hit the OpenET quota, so dev/test default to off. Deploy
    # sets SCHEDULER_ENABLED=true on exactly one single-worker process —
    # APScheduler has no cross-process lock, N workers = N duplicate runs.
    scheduler_enabled: bool = False
    scheduler_timezone: str = "America/Los_Angeles"
    # Per-IP request throttling (slowapi). Disable in tests so the suite
    # can fire many requests without tripping 429s.
    rate_limit_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @model_validator(mode="after")
    def _require_db_config(self) -> "Settings":
        """Require either a full DATABASE_URL or every discrete DB_* var."""
        if self.database_url is None:
            missing = [
                name
                for name in ("db_user", "db_password", "db_host", "db_name", "db_port")
                if getattr(self, name) is None
            ]
            if missing:
                raise ValueError("set DATABASE_URL, or all of: " + ", ".join(missing))
        return self

    @model_validator(mode="after")
    def _samesite_none_requires_secure(self) -> "Settings":
        if self.cookie_samesite == "none" and not self.secure_cookie:
            raise ValueError(
                "cookie_samesite='none' requires secure_cookie=true "
                "(browsers reject SameSite=None cookies without Secure)"
            )
        return self

    @property
    def sqlalchemy_url(self) -> str:
        """Final connection string for both the app engine and alembic."""
        if self.database_url is not None:
            return _normalize_db_url(self.database_url.get_secret_value())
        # _require_db_config guarantees the discrete vars are present here.
        assert self.db_password is not None
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password.get_secret_value()}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
