from fastapi import FastAPI, HTTPException
from typing import List, Union
from .notifier import notifier
from .config import settings
from .models import AlertManagerAlert, AlertManagerPayload, UnifiedAlert
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value and value.strip():
            return value.strip()
    return None


def _map_alertmanager_alert(
    alert: AlertManagerAlert,
    payload: AlertManagerPayload,
) -> UnifiedAlert:
    labels = {**payload.commonLabels, **alert.labels}
    annotations = {**payload.commonAnnotations, **alert.annotations}

    title = _first_non_empty(labels.get("alertname"), "Alert") or "Alert"
    summary = _first_non_empty(
        annotations.get("summary"),
        annotations.get("message"),
    )
    description = _first_non_empty(
        annotations.get("description"),
        annotations.get("message"),
    )
    status = _first_non_empty(alert.status, payload.status, "firing") or "firing"
    severity = (_first_non_empty(labels.get("severity"), "info") or "info").lower()
    timestamp = _first_non_empty(alert.startsAt, alert.endsAt)

    # Keep UnifiedAlert validation satisfied for terse upstream payloads.
    if not summary and not description:
        summary = f"{title} is {status}"

    return UnifiedAlert(
        title=title,
        summary=summary,
        description=description,
        severity=severity,
        status=status,
        timestamp=timestamp,
    )

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


@app.post("/alertmanager")
async def webhook_alertmanager(payload: AlertManagerPayload) -> dict[str, str]:
    """
    Alertmanager-compatible endpoint that converts native webhook payloads
    into UnifiedAlert objects before dispatching to Discord.
    """
    if not payload.alerts:
        raise HTTPException(status_code=422, detail="No alerts provided in payload")

    try:
        alerts = [_map_alertmanager_alert(alert, payload) for alert in payload.alerts]
        await notifier.send_notifications(alerts)
    except Exception as e:
        logger.error(f"Error sending Alertmanager notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
