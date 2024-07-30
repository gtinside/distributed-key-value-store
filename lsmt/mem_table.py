from utils.model import Data
from dataclasses import dataclass

@dataclass
class MemTable:
    _data_map = dict()

    def add(self, data:Data):
        self._data_map[data.key] = data
    
    def sort_by_key(self):
        self._data_map = dict(sorted(self._data_map.items(), key = lambda item: item[0]))
    
    def get_items(self):
        self.sort_by_key()
        return self._data_map.items()

    def get_length(self):
        return len(self._data_map)
    
    def clear_cache(self):
        self._data_map.clear()

    def get_data(self, key):
        if key in self._data_map:
            return self._data_map[key]
        raise ValueError("Key is not in Memtable")

    




