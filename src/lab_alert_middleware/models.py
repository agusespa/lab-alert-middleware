from pydantic import BaseModel, Field, model_validator
from typing import Optional

class UnifiedAlert(BaseModel):
    title: str
    summary: Optional[str] = None
    description: Optional[str] = None
    severity: str = "info"  # critical, warning, info
    status: str = "firing"  # firing, resolved
    timestamp: Optional[str] = None

    @model_validator(mode='after')
    def check_content(self) -> 'UnifiedAlert':
        if not self.summary and not self.description:
            raise ValueError("Either 'summary' or 'description' must be provided")
        return self


class AlertManagerAlert(BaseModel):
    status: str = "firing"
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None


class AlertManagerPayload(BaseModel):
    receiver: Optional[str] = None
    status: str = "firing"
    alerts: list[AlertManagerAlert] = Field(default_factory=list)
    commonLabels: dict[str, str] = Field(default_factory=dict)
    commonAnnotations: dict[str, str] = Field(default_factory=dict)
