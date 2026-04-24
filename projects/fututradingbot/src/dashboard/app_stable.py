"""
FutuTradingBot Dashboard - 穩定版
確保即使 Bridge 未連接也能正常運行
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
import json
import asyncio
import logging
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger("Dashboard")

app = FastAPI(title="FutuTradingBot Dashboard", version="2.0.0")

# Static files and templates
try:
    static_path = Path(__file__).parent.parent.parent / "static"
    templates_path = Path(__file__).parent.parent.parent / "templates"
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    templates = Jinja2Templates(directory=templates_path)
    logger.info(f"✅ Templates loaded from: {templates_path}")
except Exception as e:
    logger.error(f"❌ Failed to load static files: {e}")
    # Create minimal fallback
    templates = None

# Trading data storage
class TradingData:
    def __init__(self):
        self.price = 0.0
        self.zscore = 0.0
        self.rsi = 50.0
        self.signal = "觀望"
        self.position = None
        self.trades = []
        self.last_update = datetime.now().isoformat()
    
    def get_data(self):
        return {
            "price": self.price,
            "zscore": self.zscore,
            "rsi": self.rsi,
            "signal": self.signal,
            "position": self.position,
            "trades": self.trades[-10:],
            "last_update": self.last_update
        }

trading_data = TradingData()

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """主頁面"""
    if templates:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    else:
        # Fallback HTML
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>FutuTradingBot Dashboard</title></head>
        <body>
            <h1>FutuTradingBot Dashboard</h1>
            <p>Status: Running</p>
            <p>Bridge: <span id="bridge-status">Connecting...</span></p>
            <script>
                setInterval(async () => {
                    const res = await fetch('/api/data');
                    const data = await res.json();
                    document.getElementById('bridge-status').textContent = 
                        data.connected ? 'Connected' : 'Disconnected';
                }, 2000);
            </script>
        </body>
        </html>
        """)

@app.get("/api/data")
async def get_data():
    """獲取數據"""
    return {
        **trading_data.get_data(),
        "connected": bridge_connected,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def get_status():
    """獲取狀態"""
    return {
        "status": "running",
        "bridge_connected": bridge_connected,
        "timestamp": datetime.now().isoformat()
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        while True:
            # Send current data every 2 seconds
            await websocket.send_json({
                "type": "data",
                "data": trading_data.get_data()
            })
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")

# Bridge connection status
bridge_connected = False

async def connect_to_bridge():
    """連接到 Bridge - 獨立運行，不影響 Dashboard"""
    global bridge_connected
    
    import websockets
    
    uri = "ws://127.0.0.1:8765"
    retry_delay = 3
    
    while True:
        try:
            logger.info(f"Connecting to bridge at {uri}...")
            async with websockets.connect(uri) as ws:
                bridge_connected = True
                logger.info("✅ Connected to bridge!")
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        # Update trading data from bridge
                        if "data" in data:
                            bridge_data = data["data"]
                            if "TQQQ" in bridge_data:
                                tqqq = bridge_data["TQQQ"]
                                trading_data.price = tqqq.get("price", 0)
                                trading_data.zscore = tqqq.get("zscore", 0)
                                trading_data.rsi = tqqq.get("rsi", 50)
                            if "signal" in bridge_data:
                                trading_data.signal = bridge_data["signal"]
                            trading_data.last_update = datetime.now().isoformat()
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        logger.debug(f"Message processing error: {e}")
                        
        except Exception as e:
            bridge_connected = False
            logger.warning(f"⚠️ Bridge connection lost: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)

@app.on_event("startup")
async def startup():
    """啟動時執行"""
    logger.info("=" * 50)
    logger.info("Dashboard Starting...")
    logger.info("URL: http://127.0.0.1:8080")
    logger.info("=" * 50)
    
    # 啟動 Bridge 連接任務（獨立運行，不阻塞 Dashboard）
    asyncio.create_task(connect_to_bridge())
    logger.info("✅ Bridge connection task started")

@app.on_event("shutdown")
async def shutdown():
    """關閉時執行"""
    logger.info("Dashboard shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
