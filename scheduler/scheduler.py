from dataclasses import dataclass
from lsmt.mem_table import MemTable
import json
from loguru import logger
import time
from apscheduler.schedulers.background import BackgroundScheduler
import sys

logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")

DATA_DIR = "/tmp"

@dataclass
class Scheduler:
    cache: MemTable
    flush_size:int= 4

    def init(self):
        logger.info("Initializing the schedule")
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.mem_table_flush, 'interval', seconds=60)
        scheduler.start()
    
    def mem_table_flush(self):
        logger.info("Checking if flush can be performed")
        if self.cache.get_length() >= self.flush_size:
            # Start flushing, step 1 generate unique name for index and data file
            file_name = str(round(time.time()))
            logger.info("The file name for sstable will be {}", file_name)
            index_file_name = f"{DATA_DIR}/{file_name}.index"
            data_file_name = f"{DATA_DIR}/{file_name}.data"
            start_byte, end_byte= 0, 0
            index_data = dict()
            with open(data_file_name, 'wb') as data_file:
                for key,value in self.cache.get_items():
                    data = f"{key}:{value['value']}:{value['timestamp']}".encode()
                    end_byte+=len(data)
                    index_data[key] = {"start":start_byte, "end": end_byte, "timestamp": value["timestamp"]}
                    start_byte = end_byte
                    data_file.write(data)
                with open(index_file_name, 'w') as index_file:
                    json.dump(index_data, index_file)
            logger.info("The data has been written to Mem table, clearing it now")
            self.cache.clear_cache()



    




            

