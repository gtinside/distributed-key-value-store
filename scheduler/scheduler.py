from dataclasses import dataclass
from lsmt.mem_table import MemTable
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from compaction.compaction import Compaction
from config import settings


@dataclass
class Scheduler:
    """
    The sole purpose of this scheduler is to do the following:
    1. Flush Memtable to SSTable on disk
    2. Kick off compaction, to combine multiple data and index files into one
    """
    cache: MemTable = MemTable()
    compaction: Compaction = Compaction()
    scheduler = BackgroundScheduler()

    def init(self):
        logger.info("Initializing the schedule")
        self.flush_job:Job = self.scheduler.add_job(self.trigger_mem_table_flush, 'interval', seconds=settings.memTable.schedule)
        self.compaction_job:Job = self.scheduler.add_job(self.trigger_compaction, 'interval', seconds=settings.compaction.schedule)
        self.scheduler.start()
    
    def trigger_mem_table_flush(self):
        logger.info("Time to trigger the memtable flush, checking the condition...")
        if self.cache.can_flush():
            self.cache.flush()

    def trigger_compaction(self):
        if self.compaction.can_compact():
            logger.info("Time to trigger compaction, flush needs to stop to avoid race conditions")
            self.flush_job.pause()
            self.compaction.compact()
            logger.info("Compacting complete, enabling the mem flush again")
            self.flush_job.resume()

    




            

