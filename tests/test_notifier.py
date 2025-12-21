import pytest
from unittest.mock import AsyncMock, patch
from lab_alert_middleware.notifier import DiscordNotifier
from lab_alert_middleware.models import UnifiedAlert
import httpx

def test_format_unified_firing():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    alert = UnifiedAlert(
        title="TestAlert",
        summary="This is a summary",
        description="This is a description",
        severity="critical",
        status="firing",
        timestamp="2023-01-01T00:00:00Z"
    )
    
    formatted = notifier.format_embed(alert)
    
    assert "🔥 CRITICAL: TestAlert" in formatted["title"]
    assert formatted["description"] == "This is a summary"
    assert formatted["color"] == 0xFF0000
    assert any(field["name"] == "Details" and field["value"] == "This is a description" for field in formatted["fields"])

def test_format_unified_resolved():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    alert = UnifiedAlert(
        title="TestAlert",
        severity="critical",
        status="resolved",
        summary="This is a summary"
    )
    
    formatted = notifier.format_embed(alert)
    
    assert "✅ RESOLVED: TestAlert" in formatted["title"]
    assert formatted["color"] == 0x2ecc71

def test_format_unified_description_only():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    alert = UnifiedAlert(
        title="SimpleAlert",
        description="This is just a description",
        severity="info"
    )
    
    formatted = notifier.format_embed(alert)
    
    assert "ℹ️ INFO: SimpleAlert" in formatted["title"]
    assert formatted["description"] == "This is just a description"
    assert not any(field["name"] == "Details" for field in formatted["fields"])

def test_format_battery_temperature_unified():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    alert = UnifiedAlert(
        title="BatteryTemperature",
        summary="Battery fire risk",
        description="Battery at 55°C on lab-pc-1. Shut down immediately and remove battery!",
        severity="critical",
        status="firing",
        timestamp="2023-12-20T07:48:14Z"
    )
    
    formatted = notifier.format_embed(alert)
    
    assert "🔥 CRITICAL: BatteryTemperature" in formatted["title"]
    assert formatted["description"] == "Battery fire risk"
    assert any(field["name"] == "Details" and "Battery at 55°C on lab-pc-1" in field["value"] for field in formatted["fields"])

def test_truncation_long_summary():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    long_summary = "A" * 5000
    alert = UnifiedAlert(
        title="LongAlert",
        summary=long_summary,
        severity="info"
    )
    
    formatted = notifier.format_embed(alert)
    
    assert len(formatted["description"]) <= 4096
    assert formatted["description"].endswith("...")

def test_truncation_long_description():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    long_description = "B" * 2000
    alert = UnifiedAlert(
        title="LongAlert",
        summary="Short summary",
        description=long_description,
        severity="info"
    )
    
    formatted = notifier.format_embed(alert)
    
    details_field = next((f for f in formatted["fields"] if f["name"] == "Details"), None)
    assert details_field is not None
    assert len(details_field["value"]) <= 1024
    assert details_field["value"].endswith("...")

def test_truncation_long_title():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    long_title = "T" * 300
    alert = UnifiedAlert(
        title=long_title,
        summary="Summary",
        severity="info"
    )
    
    formatted = notifier.format_embed(alert)
    
    assert len(formatted["title"]) <= 256
    assert formatted["title"].endswith("...")

def test_invalid_timestamp_fallback():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    alert = UnifiedAlert(
        title="BadTimestamp",
        summary="Test",
        timestamp="not-a-valid-timestamp"
    )
    
    formatted = notifier.format_embed(alert)
    
    # Should have a valid timestamp (current time fallback)
    assert "timestamp" in formatted
    assert formatted["timestamp"] is not None

@pytest.mark.asyncio
async def test_send_notifications_success():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        
        alerts = [UnifiedAlert(title="Test", summary="Test alert")]
        await notifier.send_notifications(alerts)
        
        assert mock_client.post.called

@pytest.mark.asyncio
async def test_send_notifications_http_error():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    
    mock_response = AsyncMock()
    mock_response.status_code = 429
    mock_response.json = AsyncMock(return_value={"message": "Rate limited"})
    mock_response.text = "Rate limited"
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Rate limited", 
                request=AsyncMock(), 
                response=mock_response
            )
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        
        alerts = [UnifiedAlert(title="Test", summary="Test alert")]
        
        with pytest.raises(Exception) as exc_info:
            await notifier.send_notifications(alerts)
        
        assert "429" in str(exc_info.value)

@pytest.mark.asyncio
async def test_send_notifications_timeout():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        
        alerts = [UnifiedAlert(title="Test", summary="Test alert")]
        
        with pytest.raises(Exception) as exc_info:
            await notifier.send_notifications(alerts)
        
        assert "timed out" in str(exc_info.value).lower()

