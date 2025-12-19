from fastapi import FastAPI, HTTPException, Request
from .notifier import notifier
from .config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

@app.post("/webhook")
@app.post("/webhook/alertmanager")
async def webhook_alertmanager(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not data or 'alerts' not in data:
        raise HTTPException(status_code=400, detail="Invalid payload: 'alerts' field missing")

    try:
        notifier.send_notifications(data['alerts'])
    except Exception as e:
        logger.error(f"Error sending Alertmanager notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok"}

@app.post("/webhook/homeassistant")
async def webhook_homeassistant(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        notifier.send_homeassistant_notification(data)
    except Exception as e:
        logger.error(f"Error sending Home Assistant notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
