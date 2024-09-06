import socket
from utils.model import Data
from kazoo.client import KazooClient
from impl.consistent_hashing import ConsistentHashingImpl
from lsmt.mem_table import MemTable
from loguru import logger
from lsmt.sstable import SSTable
from scheduler.scheduler import Scheduler
from exception.exceptions import NoDataFoundException
from prometheus_client import Counter


class Server:
    def __init__(self, zk_host, zk_port, private_ip, port) -> None:
        self.zk_connection = KazooClient(hosts=f"{zk_host}:{zk_port}")
        self.zk_connection.start()
        self._private_ip = private_ip
        self._port = port
        self._id_host_map = dict()
        self._consistent_hash = ConsistentHashingImpl()
        self._cache = MemTable()
        self._ss_table = SSTable()
        self._key_count = Counter("key_counter", "Number of keys", labelnames=["node"])
        self._scheduler = Scheduler(cache=self._cache)
        self._scheduler.init()

    def get_data_node(self, key: str):
        """
        Function that leverages the consistent hash lib to determine which node should host the data
        """
        node_id = self._consistent_hash.get_node_for_data(key)
        node_host_port = self._id_host_map[node_id]
        logger.info(f"Data Node is {node_host_port}")
        return node_host_port

    ####################################### Data Node Functions ########################################

    def add_data(self, data: Data):
        self._key_count.labels(node=self._private_ip).inc()
        return self._cache.add(data)

    def delete_data(self, key: str):
        data = self.get_data(key)
        self.add_data(Data(key=data.key, value=data.value, deleted=True))
        self._key_count.labels(node=self._private_ip).inc(-1)

    def get_data(self, key) -> Data:
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
        if event.state == "CONNECTED" and self.check_if_leader():
            logger.info("A new follower has been added")
            children = self.zk_connection.get_children("/election")
            logger.info(f"Entries found for child: {children}")
            for child in children:
                data, _ = self.zk_connection.get(f"/election/{child}")
                id = str(child).replace("n_", "")
                logger.info(f"Data associated with the child {data} and id is {id}")

                if id not in self._id_host_map:
                    self._consistent_hash.add_node(str(id))
                    self._id_host_map[id] = data.decode()

    def check_if_leader(self):
        children = self.zk_connection.get_children("/election")
        ids = sorted([int(str(child).replace("n_", "")) for child in children])
        logger.info(
            "Sorted ids %s and leader is %s, id is %s" % (ids, ids[0], self.identifier)
        )
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
            logger.info(
                "Will be storing IP: {} and port: {}", self._private_ip, self._port
            )
            child = self.zk_connection.create(
                "/election/n_",
                ephemeral=True,
                sequence=True,
                value=f"{self._private_ip}:{self._port}".encode(),
            )
            logger.info("Created ephermal node %s" % child)
            if child:
                self.identifier = int(str(child).replace("/election/n_", ""))
                self.zk_connection.get_children(
                    "/election", watch=self.watch_for_child_nodes
                )
