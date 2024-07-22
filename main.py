from fastapi import FastAPI
from server.server import Server
from contextlib import asynccontextmanager
from utils.model import Data
import socket
import logging
import uvicorn
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')


server_instance = None
port_range = [8000, 9000]


app = FastAPI()

@app.get("/nodes")
async def get_nodes():
    logging.info(server_instance.get_nodes())
    return {"Hello": "World"}

@app.post("/add/")
async def create(data: Data):
    logging.info(f"{server_instance.add_data(data)} will be responsible for this data")
    return data

@app.post("/admin/add/")
async def admin_add(data: Data):
    logging.info(f"Received a request from master to add data to add {data.key}")
    server_instance.add_data_to_cache(data)
    

if __name__ == "__main__":
    port = random.randint(port_range[0], port_range[1])
    server_instance = Server(zk_host="0.0.0.0", zk_port="2181", 
                             host=socket.gethostbyname(socket.gethostname()), port=port)
    server_instance.start()
    logging.info(f"This server will run on port: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)



