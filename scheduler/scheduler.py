from dataclasses import dataclass
import schedule
from lsmt.mem_table import MemTable
import sys
import json
from datetime import datetime 
from loguru import logger
logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")


SIZE_LIMIT = 1000 # size in bytes
DATA_DIR = "/node/"

@dataclass
class Scheduler:
    cache: MemTable

    def init(self):
        schedule.every().minute.do(self.mem_table_flush)
    
    def mem_table_flush(self):
        if sys.getsizeof(self.cache) >= SIZE_LIMIT:
            # Sort the key


            # Start flushing, step 1 generate unique name for index and data file
            file_name = str(datetime.now())
            logger.info("The file name for sstable will be {}", file_name)
            index_file_name = f"{DATA_DIR}/{file_name}.index"
            data_file_name = f"{DATA_DIR}/{file_name}.data"
            start_byte, end_byte= 0, 0
            index_data = dict()
            with open(data_file_name, 'wb') as data_file:
                self.cache = self.cache.sort_by_key()
                for key,value in self.cache.items():
                    data = f"{key}:{value}".encode()
                    end_byte+=len(data)
                    index_data[key] = {"start":start_byte, "end": end_byte}
                    start_byte = end_byte+1
                    data_file.write(data)
                with open(index_file_name, 'w') as index_file:
                    json.dump(index_file)
                    
                    



            

