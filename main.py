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


@app.post("/add/")
async def create(data: Data):
    try:
        logger.info(f"{server_instance.add_data(data)} will be responsible for this data")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error adding the data due to {str(e)}')


@app.post("/admin/add/")
async def admin_add(data: Data):
    try:
        logger.info(f"Received a request from the leader to add data for {data.key}")
        server_instance.add_data(data)
        return {"Status": "Completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error adding the data due to {str(e)}')

@app.get("/get/")
async def get_data(key: str):
    try:
        logger.info(f"Received a request for retrieving data for key: {key}")
        return server_instance.get_data(key)
    except NoDataFoundException:
        raise HTTPException(status_code=404, detail=f'No data found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting the data due to {str(e)}')

@app.post("/admin/delete")
async def delete_data(key: str):
    try:
        logger.info(f"Received a request from master to delete data for key: {key}")
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



