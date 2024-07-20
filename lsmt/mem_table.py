from utils.model import Data
from dataclasses import dataclass

@dataclass
class Memtable:
    _data_map: dict

    def add(self, data:Data):
        self._data_map[data.key] = data.value

    def get(self, key:str):
        return self._data_map.get[key]
    




