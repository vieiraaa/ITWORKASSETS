from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./ati-dev.db"
    jwt_secret: str = "development-only-change-me"
    bootstrap_admin_password: str = "admin"
    heartbeat_timeout_seconds: int = 300
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
