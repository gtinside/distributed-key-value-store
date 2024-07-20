from dataclasses import dataclass
from mem_table import Memtable

@dataclass
class SSTable:
    dir: str
    size_in_bytes: int
    mem_table: MemTable
    

