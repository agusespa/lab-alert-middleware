import pytest
from fastapi.testclient import TestClient
from lab_alert_middleware.main import app
from unittest.mock import patch

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("lab_alert_middleware.main.notifier.send_notifications")
def test_webhook_endpoint(mock_send):
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "Test", "severity": "info"},
                "annotations": {"summary": "test alert"}
            }
        ]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_send.assert_called_once()

@patch("lab_alert_middleware.main.notifier.send_homeassistant_notification")
def test_homeassistant_endpoint(mock_send):
    payload = {
        "title": "HA Alert",
        "message": "Sensor high",
        "data": {"severity": "critical"}
    }
    response = client.post("/webhook/homeassistant", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_send.assert_called_once_with(payload)
