from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from lab_alert_middleware.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("lab_alert_middleware.notifier.httpx.AsyncClient")
def test_unified_webhook(mock_client_class):
    # Mock httpx.AsyncClient to avoid actual Discord calls
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client
    
    payload = {
        "title": "Unified Test",
        "summary": "Short summary",
        "description": "Longer description here",
        "severity": "critical"
    }
    
    response = client.post("/discord-alert", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert mock_client.post.called

def test_unified_webhook_invalid_payload():
    # Attempt to send a payload with only a title (invalid as summary/description are missing)
    payload = {
        "title": "Invalid Alert"
    }
    
    response = client.post("/discord-alert", json=payload)
    assert response.status_code == 422
    assert "Either 'summary' or 'description' must be provided" in response.text

@patch("lab_alert_middleware.notifier.httpx.AsyncClient")
def test_unified_webhook_list_of_alerts(mock_client_class):
    # Test sending multiple alerts at once
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client
    
    payload = [
        {"title": "Alert 1", "summary": "First alert"},
        {"title": "Alert 2", "summary": "Second alert"}
    ]
    
    response = client.post("/discord-alert", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
