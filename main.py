from fastapi import FastAPI
from server.server import Server
from contextlib import asynccontextmanager
from utils.model import Data

server_instance:Server = Server(zk_host="0.0.0.0", zk_port="2181")

@asynccontextmanager
async def init(app: FastAPI):
    server_instance.start()
    yield

app = FastAPI(lifespan=init)

@app.get("/nodes")
async def get_nodes():
    print(server_instance.get_nodes())
    return {"Hello": "World"}

@app.post("/add/")
async def create(data: Data):
    print(server_instance.add_data(data))
    return data

