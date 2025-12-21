import pytest
from pydantic import ValidationError
from lab_alert_middleware.config import Settings


def test_valid_discord_webhook_url():
    # Test valid Discord webhook URL
    settings = Settings(discord_webhook_url="https://discord.com/api/webhooks/123/abc")
    assert settings.discord_webhook_url == "https://discord.com/api/webhooks/123/abc"


def test_valid_discordapp_webhook_url():
    # Test valid old-style Discord webhook URL
    settings = Settings(discord_webhook_url="https://discordapp.com/api/webhooks/123/abc")
    assert settings.discord_webhook_url == "https://discordapp.com/api/webhooks/123/abc"


def test_invalid_webhook_url():
    # Test invalid webhook URL
    with pytest.raises(ValidationError) as exc_info:
        Settings(discord_webhook_url="https://example.com/webhook")
    
    assert "discord_webhook_url must be a valid Discord webhook URL" in str(exc_info.value)


def test_missing_webhook_url():
    # Test missing required webhook URL - env var is set in conftest, so we need to clear it
    import os
    old_value = os.environ.pop("DISCORD_WEBHOOK_URL", None)
    try:
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "discord_webhook_url" in str(exc_info.value)
    finally:
        if old_value:
            os.environ["DISCORD_WEBHOOK_URL"] = old_value


def test_default_values():
    # Test default values for optional settings
    settings = Settings(discord_webhook_url="https://discord.com/api/webhooks/123/abc")
    assert settings.host == "0.0.0.0"
    assert settings.port == 5001
    assert settings.app_name == "lab-alert-middleware"
