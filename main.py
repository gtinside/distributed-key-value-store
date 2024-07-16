from fastapi import FastAPI
from server.server import Server
from contextlib import asynccontextmanager
from utils.model import Data
import socket
import logging
import uvicorn

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')


server_instance = None

@asynccontextmanager
async def init(app: FastAPI):
    server_instance = Server(zk_host="0.0.0.0", zk_port="2181", 
                             host=socket.gethostbyname(socket.gethostname()), port=8000)
    server_instance.start()
    yield

app = FastAPI(lifespan=init)

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
    logging.info("Received a request from master to add data")
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



