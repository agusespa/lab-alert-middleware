import pytest
from lab_alert_middleware.notifier import DiscordNotifier

def test_format_alert_firing():
    notifier = DiscordNotifier(webhook_url="http://mock-webhook")
    alert = {
        "status": "firing",
        "labels": {
            "alertname": "TestAlert",
            "severity": "critical",
            "service": "backend"
        },
        "annotations": {
            "summary": "This is a summary",
            "description": "This is a description"
        },
        "startsAt": "2023-01-01T00:00:00Z"
    }
    
    formatted = notifier.format_alert(alert)
    
    assert "🔥 CRITICAL: TestAlert" in formatted["title"]
    assert formatted["description"] == "This is a summary"
    assert formatted["color"] == 0xFF0000
    assert any(field["name"] == "Details" and field["value"] == "This is a description" for field in formatted["fields"])
    assert any(field["name"] == "Tags" and "**service**: backend" in field["value"] for field in formatted["fields"])

def test_format_alert_resolved():
    notifier = DiscordNotifier(webhook_url="http://mock-webhook")
    alert = {
        "status": "resolved",
        "labels": {
            "alertname": "TestAlert",
            "severity": "critical"
        },
        "annotations": {
            "summary": "This is a summary"
        }
    }
    
    formatted = notifier.format_alert(alert)
    
    assert "✅ RESOLVED: TestAlert" in formatted["title"]
    assert formatted["color"] == 0x00FF00

def test_format_homeassistant_notification():
    notifier = DiscordNotifier(webhook_url="http://mock-webhook")
    data = {
        "title": "HA Title",
        "message": "HA Message",
        "data": {
            "severity": "warning"
        }
    }
    
    formatted = notifier.format_homeassistant_notification(data)
    
    assert formatted["title"] == "HA Title"
    assert formatted["description"] == "HA Message"
    assert formatted["color"] == 0xFFA500
    assert formatted["footer"]["text"] == "Source: Home Assistant"
