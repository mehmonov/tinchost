from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
import psutil
import time
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import aiofiles

app = FastAPI(title="TincHost System Monitor")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

class SystemMonitor:
    def __init__(self):
        self.log_file = Path("logs/system.log")
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_system_stats(self) -> Dict[str, Any]:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used": memory.used // (1024**3),
            "memory_total": memory.total // (1024**3),
            "disk_percent": disk.percent,
            "disk_used": disk.used // (1024**3),
            "disk_total": disk.total // (1024**3),
            "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "warning"
        }

    async def get_recent_logs(self, lines: int = 50) -> List[str]:
        if not self.log_file.exists():
            return []
        
        async with aiofiles.open(self.log_file, 'r') as f:
            content = await f.read()
            return content.strip().split('\n')[-lines:]

monitor = SystemMonitor()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("log_monitor.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            stats = monitor.get_system_stats()
            logs = await monitor.get_recent_logs()
            
            message = {
                "type": "system_update",
                "data": {
                    "stats": stats,
                    "logs": logs
                }
            }
            
            await manager.broadcast(message)
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/stats")
async def get_stats():
    return monitor.get_system_stats()

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    logs = await monitor.get_recent_logs(lines)
    return {"logs": logs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)