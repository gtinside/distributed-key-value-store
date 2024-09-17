# CoreCache

CoreCache is a distributed key-value store designed for high performance and scalability.

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/gtinside/distributed-key-value-store/validate.yaml?style=plastic&label=Unit%20Tests) 
![GitHub Release](https://img.shields.io/github/v/release/gtinside/distributed-key-value-store?style=plastic&color=red) 
![GitHub Issues](https://img.shields.io/github/issues/gtinside/distributed-key-value-store?style=plastic) 
![GitHub Closed Issues](https://img.shields.io/github/issues-pr-closed/gtinside/distributed-key-value-store?style=plastic&color=blue) 
![GitHub Commit Activity](https://img.shields.io/github/commit-activity/w/gtinside/distributed-key-value-store?style=plastic&color=orange) 
![GitHub License](https://img.shields.io/github/license/gtinside/distributed-key-value-store?style=plastic)

## Features

CoreCache MVP includes the following features:
1. **Leader Election and Coordination**: Managed through ZooKeeper.
2. **Data Handling**: Reads and writes are processed through a leader node.
3. **Data Storage**: Utilizes a Log-Structured Merge Tree (LSM Tree) for efficient data storage.
4. **API Support**: Provides GET, PUT, and DELETE operations.
5. **Data Management**: Memtables handle data until it is flushed to SSTable, and deletions are managed during compaction.

### Not Included in MVP
- **Replicas**: Data replication is not implemented in the MVP.
- **Write-Ahead Logs (WAL)**: WAL is not included.

### Memtable and SSTable
- Data is first read from and written to Memtables.
- Memtables are flushed to SSTables, at which point they are cleared.
- **DELETE Operations**: Data is marked for deletion and collected during compaction.
- **Compaction Role**: Handles updates and deletions by rewriting index and data files.

## Dependencies

CoreCache requires the following dependencies:
1. **Kazoo**: A library for interacting with ZooKeeper.
2. **dynaconf**: Manages Python dependencies and configuration.
3. **Colima**: Recommended for local development (alternative to Docker).

## Running Locally

To run CoreCache locally:
1. **Start ZooKeeper**: Use the following Docker command to run ZooKeeper in a container.
    ```bash
    docker run --name some-zookeeper -p 2181:2181 --restart always -d zookeeper
    ```
2. **Connect to ZooKeeper**: Use the following command to connect to the ZooKeeper container.
    ```bash
    docker run -it --rm --link some-zookeeper:zookeeper zookeeper zkCli.sh -server zookeeper
    ```

## Deploying CoreCache

Follow these steps to deploy CoreCache:
1. Ensure that Python and pip are installed on your system.
2. Download the CoreCache release.
    ```bash
    curl -L -o corecache-0.11.tar.gz https://github.com/gtinside/distributed-key-value-store/archive/refs/tags/0.11.tar.gz
    ```
3. Extract the downloaded file.
    ```bash
    tar -xvzf corecache-0.11.tar.gz
    ```
4. **Run ZooKeeper**: Ensure ZooKeeper is running.
5. Navigate to the scripts directory.
    ```bash
    cd distributed-key-value-store-0.11/scripts
    ```
6. Start the CoreCache server.
    ```bash
    start_server.sh --zooKeeperHost localhost --zooKeeperPort 2181
    ```

## Benchmarks

Here are some performance benchmarks:

| Date       | CoreCache Version | Number of Nodes | Configuration | Operation | Total Requests | Max Throughput   | Avg Latency | p95 Latency | Detailed Report |
|------------|-------------------|-----------------|---------------|-----------|----------------|------------------|-------------|-------------|-----------------|
| 09/16/2024 | v0.15             | 3               | AWS t2.micro   | POST      | 10K            | 31.2 requests/sec | 3.53 ms     | 12.2 ms     | [More Details](./load-tests/v0.15/Load%20Testing%20(09:16)%20-%2016%20Sep,%2000:44%20-%20Dashboards%20-%20Grafana.pdf) |

## Limitations

CoreCache has few limitations that being actively addressed:
- **Race Conditions**: Potential issues when data is being inserted while the cache is being flushed to SSTable.
- **Configuration Management**: Configuration items such as data directory, port range, and flush conditions should be managed via a properties file.
- **Data Retrieval**: Only the searched key is made available in Memcache when retrieving data from SSTable.
- **Single Leader**: Only the leader node can insert data into the cache.
- **MemTable Flush**: This process stops the world, potentially halting data insertion during a flush.
- **Index File Scanning**: Empty MemTable requires scanning all index files to locate data, which could be optimized.
- **Timestamp Accuracy**: Timestamp on data should reflect when the key-value pair was first inserted.
- **Dependency Management**: Consider migrating to Poetry for improved dependency management.
- **Error Handling**: Implement proper error handling across all APIs.
- **Pathlib Migration**: Migrate file manipulations to `pathlib`.
- **Data Integrity**: If a key marked as deleted (`deleted=true`) is not flushed before a node crash, the key remains undeleted. This can be mitigated with a Write-Ahead Log (WAL).

