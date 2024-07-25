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
7. Data is read from and written to Memtables
8. Once flushed to SSTable, Memtables are emptied


## Dependencies
1. Kazoo - lib for dealing with ZooKeeper


## Running this locally
1. Run Zookeeper, feel free to use the containerized version
```
docker run --name some-zookeeper -p 2181:2181 --restart always -d zookeeper
```
2. To connect to ZooKeeper runnning in a container
```
docker run -it --rm --link some-zookeeper:zookeeper zookeeper zkCli.sh -server zookeeper
```

## Limitations
- Race condition, if the data is getting inserted into cache and cache becomes qualified for a flush to SSTable. 
- Configuration items such as data directory, port range, flush condition should all come from a properties file.
- When getting data from SSTable, only the searched key will be made available in the Memcache
- Only leader can insert the data in cache for now.
- MemTable flush is a stop the world process. If scheduler kicks in, it stop the application to take new data put requests
- If the MemTable (cache) is empty then each index file has to be read to figure out which data file contains the data. This is not bad but there might be a better way to reduce the number of index files that needs to be scanned
- Timestamp on 'Data' is incorrect. Should be the time when key,value was first inserted into cache
