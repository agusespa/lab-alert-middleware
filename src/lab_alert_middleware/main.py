from fastapi import FastAPI, HTTPException
from typing import List, Union
from .notifier import notifier
from .config import settings
from .models import UnifiedAlert
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

@app.post("/discord-alert")
async def webhook_unified(alerts: Union[UnifiedAlert, List[UnifiedAlert]]) -> dict[str, str]:
    """
    Unified webhook endpoint that accepts a single alert or a list of alerts
    in the standard internal format.
    """
    try:
        if isinstance(alerts, UnifiedAlert):
            alerts = [alerts]
        await notifier.send_notifications(alerts)
    except Exception as e:
        logger.error(f"Error sending unified notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
