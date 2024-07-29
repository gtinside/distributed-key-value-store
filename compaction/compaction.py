from dataclasses import dataclass
import glob
from loguru import logger
import json

DATA_DIR = "/tmp"

@dataclass
class Compaction:
    '''
    Compaction is triggered by Scheduler and does the following
    1. Check the number of data files, if the number is greater than thereshold then compacts them
    2. Compaction process 
        a) Read the data files one by one, identify updates and deletes
        b) Write another set of index and data files 
        c) Rename the existing index and files
    '''
    max_data_files: int = 2

    def compact(self):
        key_offset_map = dict()
        num_of_files = glob.glob(DATA_DIR/"*.index")
        if len(num_of_files) > self.compact:
            logger.info("Files are more the required limit, compaction can be done")
            for index_file in num_of_files:
                with open(index_file, 'r') as f_index_file:
                    index_data = json.load(f_index_file)
                    


    