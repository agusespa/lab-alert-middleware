import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from lab_alert_middleware.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("requests.post")
def test_unified_webhook(mock_post):
    # Mock requests.post to avoid actual Discord calls
    mock_post.return_value = MagicMock(status_code=200)
    
    payload = {
        "title": "Unified Test",
        "summary": "Short summary",
        "description": "Longer description here",
        "severity": "critical"
    }
    
    response = client.post("/discord-alert", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert mock_post.called

def test_unified_webhook_invalid_payload():
    # Attempt to send a payload with only a title (invalid as summary/description are missing)
    payload = {
        "title": "Invalid Alert"
    }
    
    response = client.post("/discord-alert", json=payload)
    assert response.status_code == 422
    assert "Either 'summary' or 'description' must be provided" in response.text
