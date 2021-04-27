from typing import Optional, Tuple
from pydantic import BaseModel
import enum

class NotificationTo(enum.Enum):
    GPS = "GPS"
    LOCK = "LOCK"

class Notification(BaseModel):
    title: str
    message: str
    to: NotificationTo