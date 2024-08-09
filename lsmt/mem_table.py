from utils.model import Data
from dataclasses import dataclass
from config import settings
from loguru import logger
from exception.exceptions import NoDataFoundException
import time
import json

@dataclass
class MemTable:
    data_map: dict

    def add(self, data:Data):
        self.data_map[data.key] = data
    
    def sort_by_key(self):
        self.data_map = dict(sorted(self.data_map.items(), key = lambda item: item[0]))
    
    def get_items(self):
        self.sort_by_key()
        return self.data_map.items()

    def get_length(self):
        return len(self.data_map)
    
    def clear_cache(self):
        self.data_map.clear()

    def get_data(self, key):
        if key in self.data_map and not self.data_map[key].deleted:
            return self.data_map[key]
        raise NoDataFoundException("Key is not in Memtable")
    
    def can_flush(self) -> bool:
        return self.get_length() >= settings.memTable.numOfRecords

    def flush(self):
        """
        Function is responsible for flushing the Memtable to SSTable
        """
        # Start flushing, step 1 generate unique name for index and data file
        data_dir = settings.dataDirectory
        file_name = str(round(time.time()))
        logger.info("The file name for sstable will be {}", file_name)
        index_file_name = f"{data_dir}/{file_name}.index"
        data_file_name = f"{data_dir}/{file_name}.data"
        start_byte, end_byte= 0, 0
        index_data = dict()
        with open(data_file_name, 'wb') as data_file:
            for key,user_data in self.get_items():
                data = f"{key}:{user_data.value}:{user_data.timestamp}:{user_data.deleted}".encode()
                end_byte+=len(data)
                index_data[key] = {"start":start_byte, "end": end_byte, "timestamp": user_data.timestamp, "deleted": user_data.deleted}
                start_byte = end_byte
                data_file.write(data)
            with open(index_file_name, 'w') as index_file:
                json.dump(index_data, index_file)
        logger.info("The data has been written to Mem table, clearing it now")
        self.clear_cache()


    




