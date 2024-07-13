from kazoo.client import KazooClient
from kazoo.recipe.election import Election
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

class Server:
   def __init__(self, zk_host, zk_port) -> None:
      self.zk_connection = KazooClient(hosts=f"{zk_host}:{zk_port}")
      self.zk_connection.start()
      
  
   
   def init_leader(self):
      logging.info(f"{self.identifier} has been chosen as the leader setting it up")

   def get_nodes(self):
      return self.zk_connection.get("/election")

   def watch_for_child_nodes(self, event):
      logging.info("Looks like children changed")
      children = self.zk_connection.get_children("/election")
      ids = sorted([int(str(child).replace("n_", "")) for child in children])
      logging.info("Sorted ids %s" % ids)
      logging.info("The leader is %s" % ids[0])
   

   def start(self):
      logging.info("======== Starting server, may lord have mercy ===========")
      # Step 1: Create root node
      if self.zk_connection.ensure_path("/election"):
         # Step 2: Create a ephermal and sequence node
         child = self.zk_connection.create("/election/n_", ephemeral=True, sequence=True)
         logging.info("Created ephermal node %s" % child)
         if child:
            self.identifier = child
            self.zk_connection.get_children("/election", watch=self.watch_for_child_nodes)
   

      


   







