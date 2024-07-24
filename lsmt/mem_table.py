from utils.model import Data
from dataclasses import dataclass

@dataclass
class MemTable:
    _data_map = dict()

    def add(self, data:Data):
        self._data_map[data.key] = {"value": data.value, "timestamp": data.timestamp}
    
    def sort_by_key(self):
        self._data_map = dict(sorted(self._data_map.items(), key = lambda item: item[0]))
        return self._data_map

    def get_length(self):
        return len(self._data_map)
    
    def clear_cache(self):
        self._data_map.clear()

    def get_data(self, key):
        if key in self._data_map:
            return Data(key, self._data_map[key]["value"], self._data_map[key]["timestamp"])
        raise ValueError("Key is not in Memtable")

    




