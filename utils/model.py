from pydantic import BaseModel
import time
from enum import IntEnum
from datetime import datetime

class Data(BaseModel):
    key: str
    value: str
    timestamp: int = int(round(time.time()))
    