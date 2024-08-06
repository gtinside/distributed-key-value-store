from dataclasses import dataclass
from lsmt.mem_table import MemTable
import json
from loguru import logger
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
import sys
from compaction.compaction import Compaction
from config import settings


@dataclass
class Scheduler:
    cache: MemTable
    flush_size:int= settings.memTable.numOfRecords
    scheduler = BackgroundScheduler()
    data_dir = settings.dataDirectory

    def init(self):
        logger.info("Initializing the schedule")
        self.flush_job:Job = self.scheduler.add_job(self.mem_table_flush, 'interval', seconds=settings.memTable.schedule)
        self.compaction_job:Job = self.scheduler.add_job(Compaction().compact(), 'interval', seconds=settings.compation.schedule)
        self.scheduler.start()
    
    def mem_table_flush(self):
        logger.info("Checking if flush can be performed")
        if self.cache.get_length() >= self.flush_size:
            # Start flushing, step 1 generate unique name for index and data file
            file_name = str(round(time.time()))
            logger.info("The file name for sstable will be {}", file_name)
            index_file_name = f"{self.data_dir}/{file_name}.index"
            data_file_name = f"{self.data_dir}/{file_name}.data"
            start_byte, end_byte= 0, 0
            index_data = dict()
            with open(data_file_name, 'wb') as data_file:
                for key,user_data in self.cache.get_items():
                    data = f"{key}:{user_data.value}:{user_data.timestamp}:{user_data.deleted}".encode()
                    end_byte+=len(data)
                    index_data[key] = {"start":start_byte, "end": end_byte, "timestamp": user_data.timestamp, "deleted": user_data.deleted}
                    start_byte = end_byte
                    data_file.write(data)
                with open(index_file_name, 'w') as index_file:
                    json.dump(index_data, index_file)
            logger.info("The data has been written to Mem table, clearing it now")
            self.cache.clear_cache()
        
    
    def trigger_compaction(self):
        logger.info("Time to trigger compaction, flush needs to stop to avoid race conditions")
        self.flush_job.pause()
        Compaction().compact()
        logger.info("Enabling flush again")
        self.flush_job.resume()

    




            

