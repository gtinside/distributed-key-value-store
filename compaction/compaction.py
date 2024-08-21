from dataclasses import dataclass
import glob
from loguru import logger
import json
from collections import defaultdict
import time
from config import settings
import os


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
    max_data_files: int = settings.compaction.numOfFiles
    data_dir:str = settings.dataDirectory

    def can_compact(self) -> bool:
        index_files = glob.glob(f"{self.data_dir}/*.index")
        return len(index_files) >= self.max_data_files
            
    def compact(self):
        key_offset_map = dict()
        file_key_map = defaultdict(set)
        
        # list of index files
        index_files = glob.glob(f"{self.data_dir}/*.index")
        self.prepare_data(index_files=index_files, key_offset_map=key_offset_map, 
                            file_key_map=file_key_map)
        logger.info("Data is ready to be compacted")
        self.create_compacted_files(file_key_map=file_key_map, key_offset_map=key_offset_map, index_files=index_files)
        
    def prepare_data(self, index_files, key_offset_map, file_key_map):
        """
        This function iterates through the index files and identify the keys that are
        eligible for compaction, which includes updates and deletes
        
        index_files: List of index files
        deleted_keys: List of deleted keys
        key_offset_map: Map of keys that needs to be compacted and the corresponding 
            offset in data file
        file_key_map: Map of data files and the associated keys that needs to be read
        """
        deleted_keys = set()
        for index_file in index_files:
                logger.info("Working on file: {}", index_file)
                with open(index_file, 'r') as f_index_file:
                    logger.info("Working on file: {}", f_index_file)
                    index_data = json.load(f_index_file)
                    for key in index_data:
                        logger.info("Working on key: {}, for file: {}", key, f_index_file)
                        # Key might have marked as deleted from prev index files
                        if key in deleted_keys:
                            continue
                        # Check for deletes
                        if bool(index_data[key]["deleted"]):
                            deleted_keys.add(key)
                        # Check for updates first
                        elif key in key_offset_map:
                            if key_offset_map[key]["timestamp"] < index_data[key]["timestamp"]:
                                logger.info("Updated value for key: {} is available", key)
                                key_offset_map[key] = index_data[key]
                        else:
                            key_offset_map[key] = index_data[key]
                            file_key_map[f"{index_file.split('.')[0]}.data"].add(key)
        
        # One more pass to get rid of deleted keys from the file
        for deleted_key in deleted_keys:
            if deleted_key in key_offset_map:
                key_offset_map.pop(deleted_key)
                logger.info("The key:{} has been removed as it is deleted", deleted_key)
        logger.info("Total number of keys that will be deleted:{}", len(deleted_keys))

    
    def create_compacted_files(self, file_key_map, key_offset_map, index_files):
        """
        This function is responsible for reading the keys that are marked for compaction and
        write data to both index and data file

        file_key_map: Map of data files and corresponding keys that needs to read
        key_offset_map: Map of keys and start and end bytes for their data in the data file
        index_files: List of index files that needs to be processed
        """
        # Now iterating through the map and creating a combined SSTable data file
        file_id = int(time.time())
        compacted_data_file = f"{self.data_dir}/{file_id}c.data"
        compacted_index_file = f"{self.data_dir}/{file_id}c.index"
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
                        compacted_index_data[key] = {"start":c_start_byte, "end": c_end_byte, 
                                                        "timestamp": key_offset_map[key]["timestamp"], 
                                                        "deleted": key_offset_map[key]["deleted"]}
                        c_start_byte=c_end_byte
        # list of data files
        data_files = file_key_map.keys()

        with open(compacted_index_file, 'w') as fp_compacted_index_file:
            logger.info("Writing index data to file: {}", compacted_index_file)
            json.dump(compacted_index_data, fp_compacted_index_file)
            logger.info(f"Moving {len(data_files)} data files and {len(index_files)} index files to backup")
            for index_file, data_file in index_files, data_files:
                logger.info(f"Renaming {index_file} and {data_file}")
                os.rename(index_file, f"{index_file}.backup")
                os.rename(data_file, f"{data_file}.backup")
            
        logger.info("Compaction Summary -> # of files compacted: {}, # of keys written: {}", 
                        len(file_key_map), len(compacted_index_data))


            

                        

                    


    