from fastapi import FastAPI, HTTPException
from server.server import Server
from contextlib import asynccontextmanager
from utils.model import Data
import socket
from loguru import logger
import uvicorn
import random
from config import settings
from exception.exceptions import NoDataFoundException, UnauthorizedRequestException
import requests

server_instance = None
port_range = [settings.ports.startPort, settings.ports.endPort]
app = FastAPI()


@app.post("/add/")
def add(data: Data, token:str = None):
    try:
        logger.info(f"Received request for add {data.key}")
        if server_instance.check_if_leader():
            data_node_host_port = server_instance.get_data_node(data.key)
            if f"{server_instance._host}:{server_instance._port}" == data_node_host_port:
                return server_instance.add_data(data)
            else:
                req = requests.post(f"http://{data_node_host_port}/add?token=leader", 
                          json = {"key":data.key, "value": data.value, "timestamp": data.timestamp, "deleted": data.deleted})
                if req.status_code != 200:
                    raise HTTPException(f"Error adding key: {data.key}")
                return req.json()
        elif token:
            logger.info(f"Add data request from the leader for key: {data.key}")
            return server_instance.add_data(data)
        else:
            raise UnauthorizedRequestException(f'ADD requests can only be sent to the leader')
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=f'Error adding the data due to {str(e)}')
    except Exception as ae:
        raise HTTPException(status_code=500, detail=f'Error getting the data due to {str(e)}')
    
    
@app.get("/get/")
def get(key: str, token:str = None):
    try:
        logger.info(f"Received a request for retrieving data for key: {key}")
        if server_instance.check_if_leader():
            data_node_host_port = server_instance.get_data_node(key)
            if f"{server_instance._host}:{server_instance._port}" == data_node_host_port:
                return server_instance.get_data(key)
            else:
                req = requests.post(f"http://{data_node_host_port}/get?token=leader", json = {"key":key})
                if req.status_code != 200:
                    raise HTTPException(f"Error adding key: {key}")
                return req.json()
        elif token:
            return server_instance.get_data(key)
        else:
            raise UnauthorizedRequestException()
    except NoDataFoundException:
        raise HTTPException(status_code=404, detail=f'No data found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting the data due to {str(e)}')

@app.post("/delete/")
def delete(key: str, token:str = None):
    try:
        logger.info(f"Received a request for deleting data for key: {key}")
        if server_instance.check_if_leader():
            data_node_host_port = server_instance.get_data_node(key)
            if f"{server_instance._host}:{server_instance._port}" == data_node_host_port:
                return server_instance.delete_data(key)
            else:
                req = requests.post(f"http://{data_node_host_port}/delete?token=leader", json = {"key":key})
                if req.status_code != 200:
                    raise HTTPException(f"Error adding key: {key}")
                return req.json()
        elif token:
            return server_instance.delete_data(key)
        else:
            raise UnauthorizedRequestException()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error deleting the data due to {str(e)}')
    
if __name__ == "__main__":
    port = random.randint(port_range[0], port_range[1])
    server_instance = Server(zk_host=settings.zooKeeper.host, zk_port=settings.zooKeeper.port, 
                             host="127.0.0.1", port=port)
    server_instance.start()
    logger.info(f"This server will run on port: {port}")
    uvicorn.run(app, host="127.0.0.1", port=port)



