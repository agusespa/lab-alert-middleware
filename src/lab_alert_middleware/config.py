from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    discord_webhook_url: str
    host: str = "0.0.0.0"
    port: int = 5001
    app_name: str = "lab-alert-middleware"

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

settings = Settings()
