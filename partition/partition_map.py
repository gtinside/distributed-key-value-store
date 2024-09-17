from collections import defaultdict
from utils.model import Data
import json


class PartitionMap:
    """
    This is an in-memory datastructure maintained by each node to track the list of coordinator
    nodes for each key. ex
        key1: [node1, node2]
        key2: [node1, node3]
    This datastructure will make CoreCache handle a node failure.
    """

    def __init__(self) -> None:
        self._partition_map = defaultdict(set)

    def update(self, data: Data, node):
        self._partition_map.get(data.key).add(node)

    def get(self, key):
        return self._partition_map(key)
    
    def remove(self, key, node)

    def __repr__(self) -> str:
        data = json.dump(self._partition_map)
        return data
