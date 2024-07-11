from kazoo.client import KazooClient
from kazoo.recipe.election import Election
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

class Server:
   def __init__(self, identifier, zk_host, zk_port) -> None:
      self.zk_connection = KazooClient(hosts=f"{zk_host}:{zk_port}")
      self.zk_connection.start()
      self.identifier = identifier
      self.election = self.zk_connection.Election("/election", identifier=self.identifier)
   
   def init_leader(self):
      logging.info(f"{self.identifier} has been chosen as the leader setting it up")

   def get_nodes(self):
      return self.zk_connection.get("/election")


   def start(self):
      logging.info("======== Starting server, may lord have mercy ===========")
      # Step 1: Check if the leader has been selected
      self.zk_connection.create("/election", ephemeral=True)
      self.election.run(self.init_leader)


   







