from pydantic import BaseModel
from typing import Optional, Any, Dict


class SettingsUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None
    payment_gateway_config: Optional[Dict[str, Any]] = None
