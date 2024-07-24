from pydantic import BaseModel
import time

class Data(BaseModel):
    key: str
    value: str
    timestamp: int = int(round(time.time()))