from dataclasses import dataclass
import glob
from loguru import logger
import json
from collections import defaultdict
import time

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
        deleted_keys = set()
        file_key_map = defaultdict(set)
        num_of_files = glob.glob(DATA_DIR/"*.index")
        if len(num_of_files) > self.compact:
            logger.info("Files are more the required limit, compaction can be done")
            for index_file in num_of_files:
                with open(index_file, 'r') as f_index_file:
                    index_data = json.load(f_index_file)
                    for key in index_data:
                        # Check for deletes
                        if index_data[key]["timestamp"] < 0:
                            deleted_keys.add(key)
                        # Check for updates first
                        elif key in key_offset_map:
                            if key_offset_map[key]["timestamp"] < index_data[key]["timestamp"]:
                                logger.info("Updated value for key: {} is available", key)
                                key_offset_map[key] = index_data[key]
                        else:
                            key_offset_map[key] = index_data[key]
                            file_key_map[f"{index_file.split('.')[1]}.data"].add(key)
            
            # One more pass to get rid of deleted keys from the file
            for deleted_key in deleted_keys:
                if deleted_key in key_offset_map:
                    key_offset_map.pop(deleted_key)
                    logger.info("The key:{} has been removed as it is deleted", deleted_key)

            # Now iterating through the map and creating a combined SSTable data file
            file_id = int(time.time())
            compacted_data_file = f"{file_id}c.data"
            compacted_index_file = f"{file_id}c.index"
            c_start_byte = 0
            c_end_byte = 0
            compacted_index_data = dict()
            
            with open(compacted_data_file, 'wb') as fp_compacted_data_file:
                for data_file_name, keys in file_key_map.items():
                    logger.info("Iterating through data file: {}", data_file_name)
                    with open(data_file_name, "rb") as fp_data_file:
                        for key in keys:
                            start_offset = fp_data_file.seek(key_offset_map[key]["start"])
                            end_offset = fp_data_file.seek(key_offset_map[key]["end"])
                            fp_data_file.seek(start_offset)
                            data_bytes = fp_data_file.read(end_offset - start_offset)
                            c_end_byte += len(data_bytes)
                            fp_compacted_data_file.write(data_bytes)
                            compacted_index_data[key] = {"start":c_start_byte, "end": c_end_byte, "timestamp": key_offset_map[key]["timestamp"] }
            with open(compacted_index_file, 'w') as fp_compacted_index_file:
                logger.info("Writing index data to file: {}", compacted_index_file)
                json.dump(compacted_index_data, fp_compacted_index_file)

                        

                    


    