from fastapi import FastAPI, HTTPException
from server.server import Server
from utils.model import Data, PartitionMapRequest
from loguru import logger
import uvicorn
import random
import socket
from config import settings
from exception.exceptions import NoDataFoundException, UnauthorizedRequestException
import requests
import getopt, sys
from setproctitle import setproctitle
from prometheus_client import make_asgi_app
from prometheus_client import Histogram, Counter
import time
from utils.model import PartitionMapOperation
from typing import Literal
import asyncio


setproctitle("CoreCache")

# Metric for latencies
get_latency = Histogram(
    "get_latency", "End to end latency for GET Operation", labelnames=["node"]
)
add_latency = Histogram(
    "add_latency", "End to end latency for ADD Operation", labelnames=["node"]
)
del_latency = Histogram(
    "del_latency", "End to end latency for DEL Operation", labelnames=["node"]
)

server_instance = None
server_ip = settings.server.ip
port_range = [settings.server.startPort, settings.server.endPort]
app = FastAPI(debug=False)


@app.post("/add/")
def add(data: Data, token: str = None):
    try:
        start_time = time.time()
        logger.info(f"Received request for add {data.key}")
        
        if server_instance.check_if_leader():
            data_node_host_port = server_instance.get_data_node(data.key)
            if (f"{server_instance._private_ip}:{server_instance._port}" == data_node_host_port):
                stored_data = server_instance.add_data(data)
                _send_req_to_all_nodes(endpoint="update-partition-map", node_port=data_node_host_port, 
                                       payload={"key": data.key, "node": server_instance._private_ip,
                                                "port": server_instance._port,
                                                "operation": PartitionMapOperation.new,
                                            })
                return stored_data
            else:
                return _send_req_to_one_node(endpoint="add?token=leader", request_type="PUT", 
                                             payload={
                                                "key": data.key,
                                                "value": data.value,
                                                 "timestamp": data.timestamp,
                                                 "deleted": data.deleted})
        elif token:
            logger.info(f"Add data request from the leader for key: {data.key}")
            return server_instance.add_data(data)
        else:
            raise UnauthorizedRequestException(
                f"ADD requests can only be sent to the leader"
            )
    except HTTPException as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding the data due to {str(e)}"
        )
    except Exception as ae:
        raise HTTPException(
            status_code=500, detail=f"Error getting the data due to {str(ae)}"
        )
    finally:
        add_latency.labels(node=server_instance._private_ip).observe(
            time.time() - start_time
        )


@app.get("/get/")
def get(key: str, token: str = None):
    try:
        start_time = time.time()
        logger.info(f"Received a request for retrieving data for key: {key}")
        if server_instance.check_if_leader():
            data_node_host_port = server_instance.get_data_node(key)
            if (f"{server_instance._private_ip}:{server_instance._port}" == data_node_host_port):
                _send_req_to_all_nodes(endpoint="")
                return server_instance.get_data(key)
            else:
                return _send_req_to_one_node(endpoint="get?token=leader", node_port=data_node_host_port, payload={"key": key})
        elif token:
            return server_instance.get_data(key)
        
        else:
            raise UnauthorizedRequestException()
    except NoDataFoundException:
        raise HTTPException(status_code=404, detail=f"No data found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting the data due to {str(e)}"
        )
    finally:
        get_latency.labels(node=server_instance._private_ip).observe(
            time.time() - start_time
        )


@app.post("/delete/")
def delete(key: str, token: str = None):
    try:
        start_time = time.time()
        logger.info(f"Received a request for deleting data for key: {key}")
        if server_instance.check_if_leader():
            data_node_host_port = server_instance.get_data_node(key)
            if (
                f"{server_instance._private_ip}:{server_instance._port}"
                == data_node_host_port
            ):
                return server_instance.delete_data(key)
            else:
                req = requests.post(
                    f"http://{data_node_host_port}/delete?token=leader",
                    params={"key": key},
                )
                if req.status_code != 200:
                    raise HTTPException(f"{req.reason}")
                return req.json()
        elif token:
            return server_instance.delete_data(key)
        else:
            raise UnauthorizedRequestException()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting the data due to {str(e)}"
        )
    finally:
        del_latency.labels(node=server_instance._private_ip).observe(
            time.time() - start_time
        )


@app.post("/update-partition-map/")
def update_partitionq_map(request: PartitionMapRequest):
    logger.info(
        "Received request to update partition map for key: {} and node: {}",
        request.key,
        request.node_details,
    )
    try:
        server_instance.update_partiton_map(request)
        return True
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating partition map {str(e)}"
        )


RequestType = Literal["GET", "POST"]
def _send_req_to_one_node(endpoint, request_type:RequestType, payload, node_port):
    url = f"http://{node_port}/{endpoint}/"
    if request_type == 'POST':
        req = requests.post(url, json=payload)
    else:
        req = requests.get(url, params=payload)
    if req.status_code != 200: 
        raise HTTPException(f"{req.reason}")
    
    return req.json()

def _send_req_to_all_nodes(endpoint, request_type:RequestType, payload):
    response =  []
    nodes = server_instance.get_all_other_nodes()
    for node in nodes:
        url = f"http://{node}/{endpoint}/"
        if request_type == 'POST':
            req = requests.post(url, json=payload)
        else:
            req = requests.get(url, params=payload)
        if req.status_code != 200: 
            raise HTTPException(f"{req.reason}")
        response.append(req.json())

    return None
        

           





# Code for exposing Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    try:
        all_args = sys.argv
        long_options = ["zooKeeperHost=", "zooKeeperPort="]
        short_options = ["h:", "p:"]

        arguments, values = getopt.getopt(
            args=all_args[1:], longopts=long_options, shortopts=short_options
        )

        zk_host, zk_port = settings.zooKeeper.host, settings.zooKeeper.port

        for current_argument, current_value in arguments:
            if current_argument in ("-h", "--zooKeeperHost"):
                zk_host = current_value
            elif current_argument in ("-p", "--zooKeeperPort"):
                zk_port = current_value

        ip_address = socket.gethostbyname(socket.gethostname())
        port = random.randint(port_range[0], port_range[1])
        server_instance = Server(
            zk_host=zk_host, zk_port=zk_port, private_ip=ip_address, port=port
        )
        server_instance.start()
        logger.info(
            f"This server will run on host: {server_ip}, port: {port}, zookeeper host:{zk_host}, zookeeper port: {zk_port}"
        )
        uvicorn.run(app, host=server_ip, port=port)
    except Exception as e:
        logger.error(str(e))
        sys.exit(2)
