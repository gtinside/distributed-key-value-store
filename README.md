# distributed-key-value-store
A distributed messaging platform written in python

## MVP
1. Leader election and coordination via ZooKeeper
2. Read and Writes through leader 
4. Data to be stored in Log Structured Merge Tree
5. GET, PUT and DELETE APIs
6. Not available as part of MVP
    1. Compaction
    2. Replicas
    3. Write ahead logs


## Dependencies
1. Kazoo - lib for dealing with ZooKeeper


## Running this locally
1. Run Zookeeper, feel free to use the containerized version
```
docker run --name some-zookeeper -p 2181:2181 --restart always -d zookeeper
```