from fastapi import FastAPI
from server.server import Server
import random

# Reading the properties file
server_instance = Server(identifier=str(random.randint(1, 10)), zk_host="0.0.0.0", zk_port="2181")
server_instance.start()
app = FastAPI()

@app.get("/nodes")
def get_nodes():
    print(server_instance.get_nodes())
    return {"Hello": "World"}

