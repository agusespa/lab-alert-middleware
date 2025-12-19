import requests
from datetime import datetime
from typing import Any, Dict, List
from .config import settings

SEVERITY_COLORS = {
    'critical': 0xFF0000,  # Red
    'warning': 0xFFA500,   # Orange
    'info': 0x00FF00       # Green
}

SEVERITY_EMOJIS = {
    'critical': '🔥',
    'warning': '⚠️',
    'info': 'ℹ️'
}

class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def format_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        status = alert.get('status', 'firing')
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        severity = labels.get('severity', 'info')
        
        # Determine color and emoji
        color = SEVERITY_COLORS.get(severity, 0x808080)
        emoji = SEVERITY_EMOJIS.get(severity, '📊')
        
        # Build title
        if status == 'resolved':
            title = f"✅ RESOLVED: {labels.get('alertname', 'Unknown Alert')}"
            color = 0x00FF00
        else:
            title = f"{emoji} {severity.upper()}: {labels.get('alertname', 'Unknown Alert')}"
        
        # Build description
        description = annotations.get('summary', annotations.get('description', 'No description'))
        
        # Build fields
        fields = []
        
        if annotations.get('description'):
            fields.append({
                'name': 'Details',
                'value': annotations['description'][:1024],
                'inline': False
            })

        # Add labels filtering out system ones
        ignored_labels = {'alertname', 'severity', 'instance', 'job'}
        visible_labels = {k: v for k, v in labels.items() if k not in ignored_labels}
        
        if visible_labels:
            label_text = '\n'.join([f"**{k}**: {v}" for k, v in visible_labels.items()])
            fields.append({
                'name': 'Tags',
                'value': label_text[:1024],
                'inline': True
            })
        
        # Add timestamp
        starts_at = alert.get('startsAt', '')
        if starts_at:
            try:
                dt = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                timestamp = dt.isoformat()
            except Exception:
                timestamp = starts_at
        else:
            timestamp = datetime.utcnow().isoformat()
        
        return {
            'title': title,
            'description': description[:2048],
            'color': color,
            'fields': fields,
            'timestamp': timestamp,
            'footer': {
                'text': f"Severity: {severity}"
            }
        }

    def send_notifications(self, alerts: List[Dict[str, Any]]):
        embeds = [self.format_alert(alert) for alert in alerts]
        self._send_embeds(embeds)

    def send_homeassistant_notification(self, data: Dict[str, Any]):
        embed = self.format_homeassistant_notification(data)
        self._send_embeds([embed])

    def format_homeassistant_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Home Assistant payload typically contains:
        {
            "title": "Optional Title",
            "message": "The notification message",
            "data": {
                "severity": "optional severity (info, warning, critical)"
            }
        }
        """
        title = data.get('title', 'Home Assistant Notification')
        message = data.get('message', 'No message provided')
        ha_data = data.get('data', {})
        
        severity = ha_data.get('severity', 'info')
        color = SEVERITY_COLORS.get(severity, 0x2196F3) # Default HA Blue if not a known severity

        return {
            'title': title,
            'description': message,
            'color': color,
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {
                'text': 'Source: Home Assistant'
            }
        }

    def _send_embeds(self, embeds: List[Dict[str, Any]]):
        # Discord allows max 10 embeds per message
        for i in range(0, len(embeds), 10):
            batch = embeds[i:i+10]
            payload = {
                'embeds': batch,
                'username': 'HomeLab Monitor'
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

notifier = DiscordNotifier(settings.discord_webhook_url)