from utils.model import Data
from kazoo.client import KazooClient
from impl.consistent_hashing import ConsistentHashingImpl
from lsmt.mem_table import MemTable
from loguru import logger
import requests
from lsmt.sstable import SSTable
from scheduler.scheduler import Scheduler

class Server:
   def __init__(self, zk_host, zk_port, host, port) -> None:
      self.zk_connection = KazooClient(hosts=f"{zk_host}:{zk_port}")
      self.zk_connection.start()
      self._host = host
      self._port = port
      self._id_host_map = dict()
      self._consistent_hash = None
      self._cache= MemTable()
      self._ss_table = SSTable()
      self._scheduler = Scheduler(cache=self._cache)
      self._scheduler.init()
      
   
################################ Leader Node Functions ########################################
   def init_leader(self):
      logger.info(f"I - {self.identifier} have been chosen as the leader, doing the setup")
      # Step 1: Initialize a consistent hash ring
      self._consistent_hash = ConsistentHashingImpl()
      children = self.zk_connection.get_children("/election")
      for child in children:
         data, stat = self.zk_connection.get(f"/election/{child}")
         id = str(child).replace("n_", "")
         self._consistent_hash.add_node(str(id))
         self._id_host_map[id] = data.decode()
   

   def send_put_req_to_follower(self, data: Data):
      node_for_data = self._consistent_hash.get_node_for_data(data.key)
      req = requests.post(f"http://{self._host}:{self._port}/admin/add", data = {data.key:data.value})
      logger.info(f"Received the response {req.status_code}")
   
   def send_del_req_to_follower(self, key: str):
      node_for_data = self._consistent_hash.get_node_for_data(key)
      req = requests.post(f"http://{self._host}:{self._port}/admin/delete", key = key)
      logger.info(f"Received the response {req.status_code}")


####################################### Data Node Functions ########################################
   
   def add_data(self, data: Data):
      self._cache.add(data)
   
   def delete_data(self, key: str):
      data = self.get_data(key)
      self.add_data(Data(key=data.key, value=data.value, deleted=True))
      

   def get_data(self, key) -> Data:
      '''
      This function is primarily for retrieving the data from local MemTable of a node
      If the data is not found in MemTable (cache), then its retrieved from SSTables.
      Cache is warmed post the retrieval from SSTable
      '''
      try:
         return self._cache.get_data(key)
      except ValueError:
         data = self._ss_table.get_data(key)
         self._cache.add(data)
         return data
   
######################### Coordination and Discovery ###########################################

   def watch_for_child_nodes(self, event):
      logger.info("Looks like children changed")
      if self.check_if_leader():
         logger.info("I am the leader, initializing the setup")
         self.init_leader()

   def check_if_leader(self):
      children = self.zk_connection.get_children("/election")
      ids = sorted([int(str(child).replace("n_", "")) for child in children])
      logger.info("Sorted ids %s and leader is %s, id is %s" % (ids, ids[0], self.identifier))
      if ids[0] == self.identifier:
         return True
      return False

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
   

      
   



      
   

      


   







