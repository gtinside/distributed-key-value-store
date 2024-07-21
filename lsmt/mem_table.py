from utils.model import Data
from dataclasses import dataclass

@dataclass
class MemTable:
    _data_map = dict()

    def add(self, data:Data):
        self._data_map[data.key] = data.value

    def get(self, key:str):
        return self._data_map.get[key]
    
    def sort_by_key(self):
        self._data_map = dict(sorted(self._data_map.items(), key = lambda item: item[1]))
        return self._data_map
    




