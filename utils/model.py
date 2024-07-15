from pydantic import BaseModel

class Data(BaseModel):
    key: str
    value: str