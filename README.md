# CoreCache
A distributed key-value store

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/gtinside/distributed-key-value-store/validate.yaml?style=plastic&label=Unit%20Tests) ![GitHub Release](https://img.shields.io/github/v/release/gtinside/distributed-key-value-store?style=plastic&color=red) ![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/gtinside/distributed-key-value-store?style=plastic) ![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr-closed/gtinside/distributed-key-value-store?style=plastic&color=blue) ![GitHub commit activity](https://img.shields.io/github/commit-activity/w/gtinside/distributed-key-value-store?style=plastic&color=orange) ![GitHub License](https://img.shields.io/github/license/gtinside/distributed-key-value-store?style=plastic)



## Benchmarks

| Date       | CoreCache Version | Number of Nodes | Configuration | Operation | Total Number of Requests | Max Throughput | Average Latency | p95 Latency | Detailed Report |
|------------|-------------------|-----------------|---------------|-----------|--------------------------|----------------|-----------------|-------------|-----------------|
| 09/16/2024 | v0.15             | 3               | AWS t2.micro   | POST      | 10K                      | 31.2 requests/sec | 3.53 ms         | 12.2 ms     | [Insert link](#) |


## MVP
1. Leader election and coordination via ZooKeeper
2. Read and Writes through leader 
4. Data to be stored in Log Structured Merge Tree
5. GET, PUT and DELETE APIs
6. Not available as part of MVP
    1. Replicas
    2. Write ahead logs
7. Data is read from and written to Memtables
8. Once flushed to SSTable, Memtables are emptied
9. DELETE marks the data to be collected during compaction
10. Role of Compaction in MVP is to take care of updates and deletes - so effectively rewrite the index and data file


## Dependencies
1. Kazoo - lib for dealing with ZooKeeper
2. dynaconf - For managing python dependencies
3. Colima - Not a direct dependency, but recommended for local development instead of docker


## Running this locally
1. Run Zookeeper, feel free to use the containerized version
```
docker run --name some-zookeeper -p 2181:2181 --restart always -d zookeeper
```
2. To connect to ZooKeeper runnning in a container
```
docker run -it --rm --link some-zookeeper:zookeeper zookeeper zkCli.sh -server zookeeper
```

## Deploying CoreCache
1. Make sure python and pip are installed
2. ```curl -L -o corecache-0.09.tar.gz https://github.com/gtinside/distributed-key-value-store/archive/refs/tags/0.11.tar.gz```

3. ```tar -xvzf corecache-0.11.tar.gz```
4. Run ZooKeeper
5. ```cd distributed-key-value-store-0.09/scripts```
6. ```start_server.sh --zooKeeperHost localhost --zooKeeperPort 2181`


## Limitations
- Race condition, if the data is getting inserted into cache and cache becomes qualified for a flush to SSTable. 
- Configuration items such as data directory, port range, flush condition should all come from a properties file.
- When getting data from SSTable, only the searched key will be made available in the Memcache
- Only leader can insert the data in cache for now.
- MemTable flush is a stop the world process. If scheduler kicks in, it stop the application to take new data put requests
- If the MemTable (cache) is empty then each index file has to be read to figure out which data file contains the data. This is not bad but there might be a better way to reduce the number of index files that needs to be scanned
- Timestamp on 'Data' is incorrect. Should be the time when key,value was first inserted into cache
- Migrate to Poetry for better dependency management
- Source all properties from a property file
- Compaction loads data from all the files in memory and then merges, updates, deletes and create new SSTable file
- There can be a race condition when both flush to SSTable and Compaction starts at the same time
- There can also be a race condtion when SSTables are being read for a GET and being archived by Compaction at the same time 
- Proper error handling across all APIs
- All file manipulations to be migrated to pathlib
- If a Key is marked as deleted = `true` and node crashes before the data is flushed to disk, key will not be deleted. This can be solved by having a WAL. 