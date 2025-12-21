import httpx
import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List
from collections import deque
from .config import settings

from .models import UnifiedAlert

logger = logging.getLogger(__name__)

SEVERITY_COLORS = {
    'critical': 0xFF0000,   # Red
    'warning': 0xFFA500,    # Orange
    'info': 0x2196F3,       # Blue
    'resolved': 0x2ECC71    # Emerald Green
}

SEVERITY_EMOJIS = {
    'critical': '🔥',
    'warning': '⚠️',
    'info': 'ℹ️'
}

class RateLimiter:
    """Simple rate limiter for Discord webhooks (30 requests per minute)"""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
    
    async def acquire(self) -> None:
        """Wait if necessary to respect rate limits"""
        now = datetime.now(timezone.utc).timestamp()
        
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        
        if len(self.requests) >= self.max_requests:
            sleep_time = (self.requests[0] + self.window_seconds) - now + 0.1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                await self.acquire()
        
        self.requests.append(now)

class DiscordNotifier:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url
        self.rate_limiter = RateLimiter(max_requests=30, window_seconds=60)

    def format_embed(self, alert: UnifiedAlert) -> Dict[str, Any]:
        status = alert.status
        severity = alert.severity.lower()
        title_text = alert.title
        summary = alert.summary
        description_attr = alert.description
        timestamp_raw = alert.timestamp

        # Determine color and emoji
        color = SEVERITY_COLORS.get(severity, 0x808080)
        emoji = SEVERITY_EMOJIS.get(severity, '📊')
        
        # Build title and color
        if status == 'resolved':
            full_title = f"✅ RESOLVED: {title_text}"
            color = SEVERITY_COLORS['resolved']
        else:
            full_title = f"{emoji} {severity.upper()}: {title_text}"
            color = SEVERITY_COLORS.get(severity, 0x808080)
        
        # Build description & fields
        fields = []
        if summary:
            description = summary if len(summary) <= 4096 else summary[:4093] + "..."
            if description_attr:
                detail_value = description_attr if len(description_attr) <= 1024 else description_attr[:1021] + "..."
                fields.append({
                    'name': 'Details',
                    'value': detail_value,
                    'inline': False
                })
        else:
            description = description_attr or "No details provided"
            if len(description) > 4096:
                description = description[:4093] + "..."

        # Process timestamp
        if timestamp_raw:
            try:
                dt = datetime.fromisoformat(timestamp_raw.replace('Z', '+00:00'))
                timestamp = dt.isoformat()
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid timestamp format '{timestamp_raw}' for alert '{title_text}': {e}. "
                    "Using current time instead."
                )
                timestamp = datetime.now(timezone.utc).isoformat()
        else:
            timestamp = datetime.now(timezone.utc).isoformat()

        # Truncate title if needed (Discord limit: 256 chars)
        if len(full_title) > 256:
            full_title = full_title[:253] + "..."
        
        return {
            'title': full_title,
            'description': description,
            'color': color,
            'fields': fields,
            'timestamp': timestamp
        }

    async def send_notifications(self, alerts: List[UnifiedAlert]) -> None:
        embeds = [self.format_embed(alert) for alert in alerts]
        await self._send_embeds(embeds)

    async def _send_embeds(self, embeds: List[Dict[str, Any]]) -> None:
        async with httpx.AsyncClient() as client:
            for i in range(0, len(embeds), 10):
                await self.rate_limiter.acquire()
                
                batch = embeds[i:i+10]
                payload = {
                    'embeds': batch,
                    'username': 'HomeLab Monitor'
                }
                
                try:
                    response = await client.post(self.webhook_url, json=payload, timeout=10)
                    response.raise_for_status()
                    logger.info(f"Successfully sent {len(batch)} embed(s) to Discord")
                except httpx.HTTPStatusError as e:
                    error_detail = ""
                    try:
                        error_detail = e.response.json()
                    except Exception:
                        error_detail = e.response.text
                    
                    logger.error(
                        f"Discord webhook failed with status {e.response.status_code}: {error_detail}"
                    )
                    raise Exception(
                        f"Discord API error ({e.response.status_code}): {error_detail}"
                    ) from e
                except httpx.TimeoutException as e:
                    logger.error(f"Discord webhook timeout after 10s")
                    raise Exception("Discord webhook request timed out") from e
                except httpx.RequestError as e:
                    logger.error(f"Discord webhook request failed: {e}")
                    raise Exception(f"Failed to reach Discord webhook: {e}") from e

notifier = DiscordNotifier(settings.discord_webhook_url)
