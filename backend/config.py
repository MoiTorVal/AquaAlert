from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    secret_key: SecretStr
    db_user: str
    db_password: SecretStr
    db_host: str
    db_name: str
    db_port: int
    openweather_api_key: SecretStr
    next_public_api_base_url: str
    allowed_origins: list[str] = ["http://localhost:3000"]
    secure_cookie: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()