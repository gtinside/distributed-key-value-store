from fastapi import FastAPI, HTTPException
from server.server import Server
from contextlib import asynccontextmanager
from utils.model import Data
from loguru import logger
import uvicorn
import random
import socket
from config import settings
from exception.exceptions import NoDataFoundException, UnauthorizedRequestException
import requests
import getopt, sys
from setproctitle import setproctitle


setproctitle("CoreCache")

server_instance = None
server_ip = settings.server.ip
port_range = [settings.server.startPort, settings.server.endPort]
app = FastAPI()


@app.post("/add/")
def add(data: Data, token: str = None):
    try:
        logger.info(f"Received request for add {data.key}")
        if server_instance.check_if_leader():
            data_node_host_port = server_instance.get_data_node(data.key)
            if (
                f"{server_instance._host}:{server_instance._port}"
                == data_node_host_port
            ):
                return server_instance.add_data(data)
            else:
                req = requests.post(
                    f"http://{data_node_host_port}/add?token=leader",
                    json={
                        "key": data.key,
                        "value": data.value,
                        "timestamp": data.timestamp,
                        "deleted": data.deleted,
                    },
                )
                if req.status_code != 200:
                    raise HTTPException(f"{req.reason}")
                return req.json()
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
            status_code=500, detail=f"Error getting the data due to {str(e)}"
        )


@app.get("/get/")
def get(key: str, token: str = None):
    try:
        logger.info(f"Received a request for retrieving data for key: {key}")
        if server_instance.check_if_leader():
            data_node_host_port = server_instance.get_data_node(key)
            if (
                f"{server_instance._host}:{server_instance._port}"
                == data_node_host_port
            ):
                return server_instance.get_data(key)
            else:
                req = requests.get(
                    f"http://{data_node_host_port}/get?token=leader",
                    params={"key": key},
                )
                if req.status_code != 200:
                    raise HTTPException(f"{req.reason}")
                return req.json()
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


@app.post("/delete/")
def delete(key: str, token: str = None):
    try:
        logger.info(f"Received a request for deleting data for key: {key}")
        if server_instance.check_if_leader():
            data_node_host_port = server_instance.get_data_node(key)
            if (
                f"{server_instance._host}:{server_instance._port}"
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
            zk_host=zk_host,
            zk_port=zk_port,
            host=server_ip,
            port=port,
            private_ip=ip_address,
        )
        server_instance.start()
        logger.info(
            f"This server will run on host: {server_ip}, port: {port}, zookeeper host:{zk_host}, zookeeper port: {zk_port}"
        )
        uvicorn.run(app, host=server_ip, port=port)
    except Exception as e:
        logger.error(str(e))
        sys.exit(2)
