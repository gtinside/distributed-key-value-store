from utils.model import Data
from kazoo.client import KazooClient
from impl.consistent_hashing import ConsistentHashingImpl
from lsmt.mem_table import MemTable
from loguru import logger
import requests
from lsmt.sstable import SSTable
from scheduler.scheduler import Scheduler
from exception.exceptions import NoDataFoundException
import json

class Server:
   def __init__(self, zk_host, zk_port, host, port) -> None:
      self.zk_connection = KazooClient(hosts=f"{zk_host}:{zk_port}")
      self.zk_connection.start()
      self._host = host
      self._port = port
      self._id_host_map = dict()
      self._consistent_hash = ConsistentHashingImpl()
      self._cache= MemTable()
      self._ss_table = SSTable()
      self._scheduler = Scheduler(cache=self._cache)
      #self._scheduler.init()
      
   
################################ Leader Node Functions ########################################
   def get_data_node(self, key: str):
      node_id = self._consistent_hash.get_node_for_data(key)
      node_host_port = self._id_host_map[node_id]
      logger.info(f"Data Node is {node_host_port}")
      return node_host_port

   def send_add_req_to_follower(self, data: Data):
      node_id = self._consistent_hash.get_node_for_data(data.key)
      node_host_port = self._id_host_map[node_id]
      logger.info(f"Sending the request to {node_host_port}")
      req = requests.post(f"http://{node_host_port}/admin/add", 
                          json = {"key":data.key, "value": data.value, "timestamp": data.timestamp, "deleted": data.deleted})
      if req.status_code != 200:
         raise ValueError(f"Error adding {data.key}")
   
   def send_get_req_to_follower(self, key: str):
      node_id = self._consistent_hash.get_node_for_data(key)
      node_host_port = self._id_host_map[node_id]
      logger.info(f"Sending the request to {node_host_port}")
      req = requests.post(f"http://{node_host_port}/admin/get", key=key) 
      if req.status_code == 400:
         raise NoDataFoundException(f"No data found for {key}")
      elif req.status_cod == 500:
         raise ValueError(f"Internal error, not able to find the data for {key}")
      return req.json()

   
   def send_del_req_to_follower(self, key: str):
      node_id = self._consistent_hash.get_node_for_data(key)
      node_host_port = self._id_host_map[node_id]
      logger.info(f"Sending the request to {node_host_port}")
      req = requests.post(f"http://{node_host_port}/admin/delete", key = key)
      logger.info(f"Received the response {req.status_code}")
   
####################################### Data Node Functions ########################################
   
   def add_data(self, data: Data):
      return self._cache.add(data)
   
   def delete_data(self, key: str):
      data = self.get_data(key)
      self.add_data(Data(key = data.key, value = data.value, deleted=True))
      

   def get_data(self, key) -> Data:
      '''
      This function is primarily for retrieving the data from local MemTable of a node
      If the data is not found in MemTable (cache), then its retrieved from SSTables.
      Cache is warmed post the retrieval from SSTable
      '''
      data = None
      try:
         logger.info("Checking for {} in cache", key)
         data = self._cache.get_data(key)
      except NoDataFoundException:
         logger.info("Key {} not found in cache, checking in SSTable", key)
         data = self._ss_table.get_data(key)
      if data.deleted:
         raise NoDataFoundException(f"Key {key} is missing")
      return data
         
         

   
######################### Coordination and Discovery ###########################################

   def watch_for_child_nodes(self, event):
      logger.info(f"Looks like children changed, event received is {event.state}")
      if event.state == 'CONNECTED' and self.check_if_leader():
         logger.info("A new follower has been added")
         children = self.zk_connection.get_children("/election")
         for child in children:
            data, _ = self.zk_connection.get(f"/election/{child}")
            id = str(child).replace("n_", "")
            if id not in self._id_host_map:
               self._consistent_hash.add_node(str(id))
               self._id_host_map[id] = data.decode()
   

   def check_if_leader(self):
      children = self.zk_connection.get_children("/election")
      ids = sorted([int(str(child).replace("n_", "")) for child in children])
      logger.info("Sorted ids %s and leader is %s, id is %s" % (ids, ids[0], self.identifier))
      if ids[0] == self.identifier:
         return True
      return False
   
   def get_all_nodes(self):
      return self.zk_connection.get_children("/election")

############################ The beginning #######################################################

   def start(self):
      logger.info("======== Starting server, may lord have mercy ===========")
      # Step 1: Create root node
      if self.zk_connection.ensure_path("/election"):
         # Step 2: Create a ephermal and sequence node
         child = self.zk_connection.create("/election/n_", ephemeral=True, 
                                           sequence=True, value=f"{self._host}:{self._port}".encode())
         logger.info("Created ephermal node %s" % child)
         if child:
            self.identifier = int(str(child).replace("/election/n_", ""))
            self.zk_connection.get_children("/election", watch=self.watch_for_child_nodes)
   

      
   



      
   

      


   







