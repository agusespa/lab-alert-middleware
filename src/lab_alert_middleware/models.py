from pydantic import BaseModel, model_validator
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
