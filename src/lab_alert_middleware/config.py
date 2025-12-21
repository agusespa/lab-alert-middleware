from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    discord_webhook_url: str
    host: str = "0.0.0.0"
    port: int = 5001
    app_name: str = "lab-alert-middleware"

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    @field_validator('discord_webhook_url')
    @classmethod
    def validate_discord_webhook(cls, v: str) -> str:
        if not v.startswith('https://discord.com/api/webhooks/') and \
           not v.startswith('https://discordapp.com/api/webhooks/'):
            raise ValueError(
                'discord_webhook_url must be a valid Discord webhook URL '
                '(https://discord.com/api/webhooks/... or https://discordapp.com/api/webhooks/...)'
            )
        return v

settings = Settings()
