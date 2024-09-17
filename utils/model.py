from enum import Enum
from pydantic import BaseModel
import time


class PartitionMapOperation(Enum):
    new = "new"
    delete = "delete"


class Data(BaseModel):
    key: str
    value: str
    timestamp: int = int(round(time.time()))
    deleted: bool = False


class PartitionMapRequest(BaseModel):
    key: str
    node: str
    port: str
    node_details: str = f"{node}:{port}"
    operation: PartitionMapOperation
