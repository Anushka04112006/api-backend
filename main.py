from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()



nodes = []
alerts = []



class Node(BaseModel):
    name: str
    os: str
    ip: str

class Alert(BaseModel):
    node_id: int
    severity: str
    description: str



class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()


@app.get("/")
def home():
    return {"message": "API Running"}



@app.post("/nodes")
def create_node(node: Node):
    node_data = node.dict()
    node_data["id"] = len(nodes) + 1

    nodes.append(node_data)

    return {
        "message": "Node added successfully",
        "data": node_data
    }

@app.get("/nodes")
def get_nodes():
    return nodes



@app.post("/alerts")
async def create_alert(alert: Alert):

    
    if alert.node_id > len(nodes):
        return {"error": "Node not found"}

    alert_data = alert.dict()
    alert_data["id"] = len(alerts) + 1

    alerts.append(alert_data)

    # Broadcast using websocket
    await manager.broadcast(alert_data)

    return {
        "message": "Alert created",
        "data": alert_data
    }

@app.get("/alerts")
def get_alerts(severity: Optional[str] = None):

    if severity:
        filtered = [
            alert for alert in alerts
            if alert["severity"].lower() == severity.lower()
        ]
        return filtered

    return alerts



@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
