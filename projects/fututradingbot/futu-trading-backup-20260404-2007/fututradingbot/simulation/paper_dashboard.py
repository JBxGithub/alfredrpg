"""
模擬交易 Dashboard - 獨立於實盤系統
用途: 顯示模擬交易實測結果
Port: 8081 (實盤使用 8080)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, date
import json
import asyncio
import os
from pathlib import Path
import websockets
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PaperDashboard")

app = FastAPI(title="Futu Paper Trading Dashboard", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
static_path = Path(__file__).parent.parent / "static"
templates_path = Path(__file__).parent.parent / "templates"
app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=templates_path)

# Configuration
AUTH_PASSWORD = os.getenv("PAPER_DASHBOARD_PASSWORD", "paper2024")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Paper Dashboard client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Paper Dashboard client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Real-time data from paper bridge
class PaperTradingData:
    """模擬交易數據"""
    def __init__(self):
        self.position: Optional[dict] = None
        self.account = {
            "initial_capital": 100000.0,
            "available_cash": 100000.0,
            "total_assets": 100000.0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "total_trades": 0
        }
        self.tqqq_data = {
            "price": 0.0,
            "zscore": 0.0,
            "volume": 0
        }
        self.trades: List[dict] = []
        self.strategy_status = {
            "running": False,
            "name": "TQQQ Paper Trading",
            "threshold": 1.6
        }
        self.last_update = datetime.now().isoformat()
    
    def update_from_bridge(self, data: dict):
        """從 Paper Bridge 更新數據"""
        if "account" in data:
            self.account.update(data["account"])
        if "TQQQ" in data:
            self.tqqq_data.update(data["TQQQ"])
        if "position" in data:
            self.position = data["position"]
        if "trades" in data:
            self.trades = data["trades"]
        if "strategy" in data:
            self.strategy_status.update(data["strategy"])
        self.last_update = datetime.now().isoformat()
    
    def get_dashboard_data(self) -> dict:
        """獲取 Dashboard 數據"""
        return {
            "position": self.position,
            "account": self.account,
            "TQQQ": self.tqqq_data,
            "trades": self.trades,
            "strategy": self.strategy_status,
            "timestamp": self.last_update
        }

paper_data = PaperTradingData()

# Bridge WebSocket client
class PaperBridgeClient:
    """連接到 Paper Trading Bridge"""
    def __init__(self, uri: str = "ws://127.0.0.1:8766"):
        self.uri = uri
        self.ws = None
        self.connected = False
        self.running = False
    
    async def connect(self):
        """連接到 Paper Bridge"""
        while self.running:
            try:
                logger.info(f"Connecting to paper bridge at {self.uri}...")
                self.ws = await websockets.connect(self.uri)
                self.connected = True
                logger.info("Connected to paper trading bridge!")
                
                async for message in self.ws:
                    try:
                        data = json.loads(message)
                        if data.get("type") in ["initial", "data_update", "price_update"]:
                            paper_data.update_from_bridge(data.get("data", {}))
                            await manager.broadcast({
                                "type": "price_update",
                                "data": paper_data.get_dashboard_data()
                            })
                        elif data.get("type") == "trade":
                            await manager.broadcast({
                                "type": "trade",
                                "data": paper_data.get_dashboard_data()
                            })
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON from bridge")
                        
            except Exception as e:
                logger.warning(f"Paper bridge connection error: {e}")
                self.connected = False
                await asyncio.sleep(3)
    
    async def start(self):
        """啟動 bridge client"""
        self.running = True
        await self.connect()
    
    def stop(self):
        """停止 bridge client"""
        self.running = False
        if self.ws:
            asyncio.create_task(self.ws.close())

bridge_client = PaperBridgeClient()

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/data")
async def get_data():
    return paper_data.get_dashboard_data()

@app.get("/api/status")
async def get_status():
    return {
        "paper_trading": True,
        "bridge_connected": bridge_client.connected,
        "strategy": paper_data.strategy_status,
        "timestamp": datetime.now().isoformat()
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    await websocket.send_json({
        "type": "initial",
        "data": paper_data.get_dashboard_data()
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("action") == "get_data":
                await websocket.send_json({
                    "type": "data_update",
                    "data": paper_data.get_dashboard_data()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Startup event
@app.on_event("startup")
async def startup_event():
    """啟動時連接到 Paper Bridge"""
    logger.info("Starting Paper Trading Dashboard (Port 8081)...")
    asyncio.create_task(bridge_client.start())

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """關閉時斷開連接"""
    logger.info("Shutting down Paper Dashboard...")
    bridge_client.stop()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PAPER_DASHBOARD_PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)
