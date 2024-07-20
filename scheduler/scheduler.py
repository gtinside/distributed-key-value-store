from dataclasses import dataclass
import schedule
from lsmt.mem_table import MemTable
import sys
from datetime import datetime 


SIZE_LIMIT = 1000 # size in bytes
DATA_DIR = "/node/"

@dataclass
class Scheduler:
    cache: MemTable

    def init(self):
        schedule.every().minute.do(self.mem_table_flush)
    
    def mem_table_flush(self):
        if sys.getsizeof(self.cache) >= SIZE_LIMIT:
            # Start flushing, step 1 generate unique name for index and data file
            file_name = str(datetime.now())
            

