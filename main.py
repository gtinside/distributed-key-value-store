from fastapi import FastAPI, HTTPException
from server.server import Server
from contextlib import asynccontextmanager
from utils.model import Data
import socket
from loguru import logger
import uvicorn
import random
from config import settings
from exception.exceptions import NoDataFoundException

server_instance = None
port_range = [settings.ports.startPort, settings.ports.endPort]
app = FastAPI()


@app.post("/admin/add/")
async def add_request_from_leader(data: Data):
    try:
        logger.info(f"Received a request from the leader to add data for {data.key}")
        server_instance.send_add_req_to_follower(data)
        return {"Status": "Completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error adding the data due to {str(e)}')

@app.post("/admin/delete")
async def delete_request_from_leader(key: str):
    try:
        logger.info(f"Received a request from leader to delete data for key: {key}")
        server_instance.delete_data(key)
        return {"Status": "Completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error deleting the data due to {str(e)}')

@app.post("/admin/get")
async def get_request_from_leader(key: str):
    try:
        logger.info(f"Received a request for leader for retrieving data for key: {key}")
        return server_instance.send_get_req_to_follower(key)
    except NoDataFoundException:
        raise HTTPException(status_code=404, detail=f'No data found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting the data due to {str(e)}')

# The following functions will work only when node is a leader or only one node is running 
@app.post("/add/")
async def add(data: Data):
    try:
        logger.info(f"Received request for add {data.key}")
        server_instance.send_add_req_to_follower(data)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error adding the data due to {str(e)}')
    
@app.get("/get/")
async def get(key: str):
    try:
        logger.info(f"Received a request for retrieving data for key: {key}")
        return server_instance.get_data(key)
    except NoDataFoundException:
        raise HTTPException(status_code=404, detail=f'No data found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting the data due to {str(e)}')

@app.post("/delete/")
async def delete(key: str):
    try:
        logger.info(f"Received a request for deleting data: {key}")
        server_instance.delete_data(key)
        return {"Status": "Completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error deleting the data due to {str(e)}')

    
if __name__ == "__main__":
    port = random.randint(port_range[0], port_range[1])
    server_instance = Server(zk_host=settings.zooKeeper.host, zk_port=settings.zooKeeper.port, 
                             host=socket.gethostbyname(socket.gethostname()), port=port)
    server_instance.start()
    logger.info(f"This server will run on port: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)



