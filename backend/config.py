from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    secret_key: SecretStr
    db_user: str
    db_password: SecretStr
    db_host: str
    db_name: str
    db_port: int
    openet_api_key: SecretStr | None = None
    # Spatial CIMIS key for provisional ET gap-fill; unset = gap-fill off.
    cimis_app_key: SecretStr | None = None
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
    # Opt-in: jobs hit the OpenET quota, so dev/test default to off. Deploy
    # sets SCHEDULER_ENABLED=true on exactly one single-worker process —
    # APScheduler has no cross-process lock, N workers = N duplicate runs.
    scheduler_enabled: bool = False
    scheduler_timezone: str = "America/Los_Angeles"
    # Per-IP request throttling (slowapi). Disable in tests so the suite
    # can fire many requests without tripping 429s.
    rate_limit_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()