import pytest
from lab_alert_middleware.notifier import DiscordNotifier

from lab_alert_middleware.notifier import DiscordNotifier
from lab_alert_middleware.models import UnifiedAlert

def test_format_unified_firing():
    notifier = DiscordNotifier(webhook_url="http://mock-webhook")
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
    notifier = DiscordNotifier(webhook_url="http://mock-webhook")
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
    notifier = DiscordNotifier(webhook_url="http://mock-webhook")
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
    notifier = DiscordNotifier(webhook_url="http://mock-webhook")
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
