from kazoo.client import KazooClient
from kazoo.recipe.election import Election
import logging
logging.basicConfig()

class Server:
   def __init__(self, zk_host, zk_port, identifier) -> None:
      self.zk_client = KazooClient(hosts=f"{zk_host}:{zk_port}")
      self.identifier = identifier
   
   def init_leader(self):
      logging.info("The leader has been selected, setting it up")

   def start(self):
      logging.info("======== Starting server, may lord have mercy ===========")
      # Step 1: Start the Kazoo Client
      self.zk_client.start()
      # Step 2: Check if the leader has been selected
      election = self.zk_client.Election("/election", self.identifier)
      election.run(self.init_leader)
   

   




# Reading the properties file
Server(zk_host="localhost", zk_port="2181", identifier="server-1").start()


   







