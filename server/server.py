from utils.model import Data
from kazoo.client import KazooClient
from impl.consistent_hashing import ConsistentHashingImpl
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

class Server:
   def __init__(self, zk_host, zk_port) -> None:
      self.zk_connection = KazooClient(hosts=f"{zk_host}:{zk_port}")
      self.zk_connection.start()
      
   
   def init_leader(self):
      logging.info(f"I - {self.identifier} have been chosen as the leader, doing the setup")
      # Step 1: Initialize a consistent hash ring
      self._consistent_hash = ConsistentHashingImpl()
      children = self.zk_connection.get_children("/election")
      ids = sorted([int(str(child).replace("n_", "")) for child in children])
      for id in ids:
         self._consistent_hash.add_node(str(id))


   def get_nodes(self):
      return self.zk_connection.get("/election")

   def watch_for_child_nodes(self, event):
      logging.info("Looks like children changed")
      children = self.zk_connection.get_children("/election")
      ids = sorted([int(str(child).replace("n_", "")) for child in children])
      logging.info("Sorted ids %s and leader is %s, id is %s" % (ids, ids[0], self.identifier))
      if ids[0] == self.identifier:
         logging.info("I am the leader")
         self.init_leader()
   

   def start(self):
      logging.info("======== Starting server, may lord have mercy ===========")
      # Step 1: Create root node
      if self.zk_connection.ensure_path("/election"):
         # Step 2: Create a ephermal and sequence node
         child = self.zk_connection.create("/election/n_", ephemeral=True, sequence=True)
         logging.info("Created ephermal node %s" % child)
         if child:
            self.identifier = int(str(child).replace("/election/n_", ""))
            self.zk_connection.get_children("/election", watch=self.watch_for_child_nodes)
   

   def add_data(self, data: Data):
      return self._consistent_hash.get_node_for_data(data.key)
   

      


   







