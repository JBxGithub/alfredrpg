from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
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

# Import trade recorder
import sys
sys.path.append(str(Path(__file__).parent.parent))
from recorder.trade_recorder import TradeRecorder

# Import Z-Score strategy
try:
    from strategies.zscore_strategy import ZScoreStrategy, ZScoreRealtimeTrader
except ImportError:
    # Fallback if import fails
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.strategies.zscore_strategy import ZScoreStrategy, ZScoreRealtimeTrader

# Import Futu API client for real positions
try:
    from api.futu_client import FutuTradeClient, FutuQuoteClient, Market, TrdEnv
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.api.futu_client import FutuTradeClient, FutuQuoteClient, Market, TrdEnv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Futu Trading Dashboard - Z-Score Strategy (Final 2026-03-29)", version="2.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
static_path = Path(__file__).parent.parent.parent / "static"
templates_path = Path(__file__).parent.parent.parent / "templates"
app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=templates_path)

# Configuration
AUTH_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "futu2024")
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",")

# Initialize trade recorder
recorder = TradeRecorder()

# Initialize Futu clients for real data
futu_trade_client = None
futu_quote_client = None

def init_futu_clients():
    """Initialize Futu API clients"""
    global futu_trade_client, futu_quote_client
    try:
        # Initialize quote client
        futu_quote_client = FutuQuoteClient(host="127.0.0.1", port=11111)
        if futu_quote_client.connect():
            logger.info("✅ Futu Quote Client initialized")
        
        # Initialize trade client for US market
        futu_trade_client = FutuTradeClient(host="127.0.0.1", port=11111, market=Market.US)
        if futu_trade_client.connect():
            logger.info("✅ Futu Trade Client initialized")
            # Unlock trade for real account 24026693
            if futu_trade_client.unlock_trade("011087"):
                logger.info("✅ Trade interface unlocked for account 24026693")
            else:
                logger.warning("⚠️ Failed to unlock trade interface")
            
    except Exception as e:
        logger.error(f"Failed to initialize Futu clients: {e}")

# Initialize on module load
init_futu_clients()

# WebSocket connection manager for Dashboard clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Dashboard client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Dashboard client disconnected. Total: {len(self.active_connections)}")
    
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

# Real-time data from bridge - Z-Score Strategy Final (2026-03-29)
class TradingData:
    """Trading data synced from realtime bridge (Z-Score Mean Reversion Strategy)

    策略參數：
    - Z-Score 進場閾值: ±1.65
    - RSI 超買/超賣: 70/30
    - 成交量過濾: > 20日均量 × 50%
    - 止盈/止損: 5%/3%
    - 時間止損: 7天
    """
    def __init__(self):
        self.positions: Dict[str, dict] = {}
        self.account = {
            "total_assets": 100000.00,
            "available_cash": 100000.00,
            "daily_pnl": 0.00,
            "daily_pnl_pct": 0.00,
            "total_unrealized_pnl": 0.00
        }
        # TQQQ數據包含Z-Score和RSI（最終版策略）
        self.tqqq_data: Dict[str, any] = {
            "price": 0.0,
            "change": 0.0,
            "change_pct": 0.0,
            "volume": 0,
            "zscore": 0.0,
            "rsi": 50.0,
            "volume_ma": 0
        }
        self.current_signal: Optional[dict] = None
        self.signals: List[dict] = []
        self.strategy_status = {
            "running": False,
            "name": "TQQQ Long/Short Strategy (框架A)",
            "last_update": datetime.now().isoformat()
        }
        self.today_trades: List[dict] = []
        self.last_update = datetime.now().isoformat()
    
    def update_from_bridge(self, data: dict):
        """Update data from bridge - 適配框架A格式"""
        if "account" in data:
            self.account.update(data["account"])
        if "TQQQ" in data:
            self.tqqq_data.update(data["TQQQ"])
        if "positions" in data:
            self.positions = {p["symbol"]: p for p in data["positions"]}
        if "signal" in data:
            self.current_signal = data["signal"]
        if "signals" in data:
            self.signals = data["signals"]
        if "today_trades" in data:
            self.today_trades = data["today_trades"]
        if "strategy" in data:
            self.strategy_status.update(data["strategy"])
        self.last_update = datetime.now().isoformat()
    
    def get_dashboard_data(self) -> dict:
        """獲取Dashboard數據 - 框架A格式"""
        # Get real positions from Futu API
        real_positions = get_real_positions()
        real_account = get_real_account()
        real_trades = get_today_trades()
        
        # Use real data if available, otherwise use local data
        positions_list = real_positions if real_positions else list(self.positions.values())
        account_data = real_account if real_account else self.account
        today_trades_list = real_trades if real_trades else self.today_trades[-20:]
        
        total_pnl = sum(p.get("unrealized_pnl", 0) for p in positions_list)
        
        return {
            "positions": positions_list,
            "account": {
                **account_data,
                "total_unrealized_pnl": total_pnl
            },
            "TQQQ": self.tqqq_data,
            "signal": self.current_signal,
            "signals": self.signals,
            "strategy": self.strategy_status,
            "today_trades": today_trades_list,
            "timestamp": self.last_update
        }

trading_data = TradingData()

# ==================== Real Data Functions ====================

def get_real_positions() -> List[dict]:
    """Get real positions from Futu API (REAL only)"""
    if not futu_trade_client:
        return []
    
    try:
        # Only use REAL account
        ret_code, ret_data = futu_trade_client.position_list_query(trd_env=TrdEnv.REAL)
        
        if ret_code == 0 and ret_data is not None and len(ret_data) > 0:
            positions = []
            for _, row in ret_data.iterrows():
                position = {
                    "symbol": row.get("code", "").replace("US.", ""),
                    "quantity": int(row.get("qty", 0)),
                    "avg_cost": float(row.get("cost_price", 0)),
                    "current_price": float(row.get("nominal_price", 0)),
                    "unrealized_pnl": float(row.get("pl_val", 0)),
                    "unrealized_pnl_pct": float(row.get("pl_ratio", 0)) * 100,
                    "direction": "long" if int(row.get("qty", 0)) > 0 else "short"
                }
                positions.append(position)
            logger.info(f"Positions fetched from REAL: {len(positions)} positions")
            return positions
    except Exception as e:
        logger.error(f"Error fetching real positions: {e}")
    return []

def get_real_account() -> dict:
    """Get real account info from Futu API (REAL only)"""
    if not futu_trade_client:
        return {
            "total_assets": 0.00,
            "available_cash": 0.00,
            "daily_pnl": 0.00,
            "daily_pnl_pct": 0.00,
            "total_unrealized_pnl": 0.00
        }
    
    try:
        # Only use REAL account
        ret_code, ret_data = futu_trade_client.accinfo_query(trd_env=TrdEnv.REAL)
        
        if ret_code == 0 and ret_data is not None and len(ret_data) > 0:
            account_data = ret_data.to_dict("records")[0] if hasattr(ret_data, "to_dict") else ret_data[0]
            
            account = {
                "total_assets": float(account_data.get("total_assets", 0) or account_data.get("totalAsset", 0) or 0),
                "available_cash": float(account_data.get("cash", 0) or account_data.get("available_cash", 0) or 0),
                "daily_pnl": float(account_data.get("today_pl", 0) or account_data.get("today_profit_loss", 0) or 0),
                "daily_pnl_pct": float(account_data.get("today_pl_ratio", 0) or 0) * 100,
                "total_unrealized_pnl": 0.00
            }
            logger.info(f"Account fetched from REAL: Total=${account['total_assets']:.2f}")
            return account
    except Exception as e:
        logger.error(f"Error fetching real account: {e}")
    
    return {
        "total_assets": 0.00,
        "available_cash": 0.00,
        "daily_pnl": 0.00,
        "daily_pnl_pct": 0.00,
        "total_unrealized_pnl": 0.00
    }

def get_today_trades() -> List[dict]:
    """Get today's trades from Futu API (REAL only)"""
    if not futu_trade_client:
        return []
    
    try:
        # Only use REAL account
        ret_code, ret_data = futu_trade_client.order_list_query(trd_env=TrdEnv.REAL)
        
        if ret_code == 0 and ret_data is not None and len(ret_data) > 0:
            trades = []
            for _, row in ret_data.iterrows():
                # Only include filled orders from today
                order_status = row.get("order_status", "")
                if order_status == "FILLED_ALL":
                    trade = {
                        "time": str(row.get("create_time", "")).split(" ")[-1] if " " in str(row.get("create_time", "")) else str(row.get("create_time", "")),
                        "symbol": row.get("code", "").replace("US.", ""),
                        "action": "BUY" if row.get("trd_side") == "BUY" else "SELL",
                        "quantity": int(row.get("dealt_qty", 0)),
                        "price": float(row.get("dealt_avg_price", 0)),
                        "fee": float(row.get("dealt_qty", 0)) * float(row.get("dealt_avg_price", 0)) * 0.001,
                        "pnl": 0.0  # P&L calculated separately for sells
                    }
                    trades.append(trade)
            logger.info(f"Trades fetched from REAL: {len(trades)} trades")
            return trades[-20:]  # Return last 20 trades
    except Exception as e:
        logger.error(f"Error fetching today trades: {e}")
    return []

# Bridge WebSocket client
class BridgeClient:
    """Client to connect to realtime bridge"""
    def __init__(self, uri: str = "ws://127.0.0.1:8765"):
        self.uri = uri
        self.ws = None
        self.connected = False
        self.running = False
    
    async def connect(self):
        """Connect to bridge - 非阻塞式，即使失敗也繼續重試"""
        retry_count = 0
        max_retries = 100  # 最多重試 100 次
        
        while self.running and retry_count < max_retries:
            try:
                logger.info(f"Connecting to bridge at {self.uri}... (attempt {retry_count + 1})")
                self.ws = await asyncio.wait_for(
                    websockets.connect(self.uri),
                    timeout=5.0  # 5 秒超時
                )
                self.connected = True
                retry_count = 0  # 重置重試計數
                logger.info("✅ Connected to realtime bridge!")
                
                # Listen for messages
                async for message in self.ws:
                    try:
                        data = json.loads(message)
                        if data.get("type") in ["initial", "data_update", "price_update"]:
                            trading_data.update_from_bridge(data.get("data", {}))
                            # Broadcast to all dashboard clients
                            await manager.broadcast({
                                "type": "price_update",
                                "data": trading_data.get_dashboard_data()
                            })
                        elif data.get("type") == "signal":
                            # Forward signal to dashboard clients
                            await manager.broadcast({
                                "type": "signal",
                                "data": data.get("data", {})
                            })
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON from bridge")
                        
            except asyncio.TimeoutError:
                retry_count += 1
                logger.warning(f"⏳ Bridge connection timeout, retrying... ({retry_count}/{max_retries})")
                self.connected = False
                await asyncio.sleep(3)
            except Exception as e:
                retry_count += 1
                logger.warning(f"⚠️ Bridge connection error: {e}, retrying... ({retry_count}/{max_retries})")
                self.connected = False
                await asyncio.sleep(3)  # Retry after 3 seconds
        
        if retry_count >= max_retries:
            logger.error("❌ Max retries reached, giving up on bridge connection")
        logger.info("Bridge client stopped")
    
    async def start(self):
        """Start bridge client"""
        self.running = True
        await self.connect()
    
    def stop(self):
        """Stop bridge client"""
        self.running = False
        if self.ws:
            asyncio.create_task(self.ws.close())

bridge_client = BridgeClient()

# Auth dependency
async def verify_auth(request: Request):
    # IP whitelist check
    client_ip = request.client.host
    if ALLOWED_IPS and ALLOWED_IPS[0] and client_ip not in ALLOWED_IPS:
        # Check password in header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        token = auth_header.replace("Bearer ", "")
        if token != AUTH_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid password")
    
    return True

# Pydantic models
class TradeRequest(BaseModel):
    symbol: str
    quantity: int
    price: float
    order_type: str = "LIMIT"

class StrategyToggle(BaseModel):
    enabled: bool

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/data")
async def get_data(authorized: bool = Depends(verify_auth)):
    """Get dashboard data with real positions and trades"""
    return trading_data.get_dashboard_data()

@app.get("/api/real/refresh")
async def refresh_real_data(authorized: bool = Depends(verify_auth)):
    """Refresh real positions and account data from Futu API"""
    try:
        positions = get_real_positions()
        account = get_real_account()
        trades = get_today_trades()
        
        # Update trading data with real data
        if positions:
            trading_data.positions = {p["symbol"]: p for p in positions}
        if account:
            trading_data.account.update(account)
        if trades:
            trading_data.today_trades = trades
        
        # Broadcast update to all clients
        await manager.broadcast({
            "type": "data_update",
            "data": trading_data.get_dashboard_data()
        })
        
        return {
            "status": "success",
            "message": "Real data refreshed",
            "positions_count": len(positions),
            "trades_count": len(trades)
        }
    except Exception as e:
        logger.error(f"Error refreshing real data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/real/positions")
async def get_real_positions_api(authorized: bool = Depends(verify_auth)):
    """Get real positions from Futu API"""
    positions = get_real_positions()
    return {"status": "success", "positions": positions, "count": len(positions)}

@app.get("/api/real/account")
async def get_real_account_api(authorized: bool = Depends(verify_auth)):
    """Get real account info from Futu API"""
    account = get_real_account()
    return {"status": "success", "account": account}

@app.get("/api/real/trades")
async def get_real_trades_api(authorized: bool = Depends(verify_auth)):
    """Get today's real trades from Futu API"""
    trades = get_today_trades()
    return {"status": "success", "trades": trades, "count": len(trades)}

@app.post("/api/trade/buy")
async def buy_stock(request: TradeRequest, authorized: bool = Depends(verify_auth)):
    """Execute buy order"""
    trade_record = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "symbol": request.symbol,
        "action": "BUY",
        "quantity": request.quantity,
        "price": request.price,
        "fee": round(request.price * request.quantity * 0.001, 2),
        "pnl": 0.0
    }
    
    # Record to CSV
    recorder.record_trade(trade_record)
    
    # Update positions
    if request.symbol not in trading_data.positions:
        trading_data.positions[request.symbol] = {
            "symbol": request.symbol,
            "quantity": request.quantity,
            "avg_cost": request.price,
            "current_price": request.price,
            "unrealized_pnl": 0.0,
            "unrealized_pnl_pct": 0.0,
            "direction": "long"
        }
    else:
        pos = trading_data.positions[request.symbol]
        total_cost = pos["avg_cost"] * pos["quantity"] + request.price * request.quantity
        pos["quantity"] += request.quantity
        pos["avg_cost"] = round(total_cost / pos["quantity"], 2)
    
    # Update account
    total_cost = request.price * request.quantity + trade_record["fee"]
    trading_data.account["available_cash"] -= total_cost
    trading_data.account["total_assets"] = trading_data.account["available_cash"] + sum(
        p.get("current_price", 0) * p.get("quantity", 0) for p in trading_data.positions.values()
    )
    
    # Add to today's trades
    trading_data.today_trades.append(trade_record)
    
    # Broadcast update
    await manager.broadcast({
        "type": "trade_update",
        "data": trading_data.get_dashboard_data()
    })
    
    logger.info(f"BUY: {request.quantity} shares of {request.symbol} @ {request.price}")
    
    return {"status": "success", "message": f"Bought {request.quantity} shares of {request.symbol} @ {request.price}"}

@app.post("/api/trade/sell")
async def sell_stock(request: TradeRequest, authorized: bool = Depends(verify_auth)):
    """Execute sell order"""
    if request.symbol not in trading_data.positions:
        raise HTTPException(status_code=400, detail="No position found for this symbol")
    
    pos = trading_data.positions[request.symbol]
    if pos["quantity"] < request.quantity:
        raise HTTPException(status_code=400, detail="Insufficient shares to sell")
    
    # Calculate P&L
    realized_pnl = round((request.price - pos["avg_cost"]) * request.quantity, 2)
    
    trade_record = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "symbol": request.symbol,
        "action": "SELL",
        "quantity": request.quantity,
        "price": request.price,
        "fee": round(request.price * request.quantity * 0.001, 2),
        "pnl": realized_pnl
    }
    
    # Record to CSV
    recorder.record_trade(trade_record)
    
    # Update positions
    pos["quantity"] -= request.quantity
    if pos["quantity"] == 0:
        del trading_data.positions[request.symbol]
    
    # Update account
    proceeds = request.price * request.quantity - trade_record["fee"]
    trading_data.account["available_cash"] += proceeds
    trading_data.account["daily_pnl"] += realized_pnl
    trading_data.account["total_assets"] = trading_data.account["available_cash"] + sum(
        p.get("current_price", 0) * p.get("quantity", 0) for p in trading_data.positions.values()
    )
    
    # Add to today's trades
    trading_data.today_trades.append(trade_record)
    
    # Broadcast update
    await manager.broadcast({
        "type": "trade_update",
        "data": trading_data.get_dashboard_data()
    })
    
    logger.info(f"SELL: {request.quantity} shares of {request.symbol} @ {request.price}, PnL: {realized_pnl}")
    
    return {"status": "success", "message": f"Sold {request.quantity} shares of {request.symbol} @ {request.price}", "pnl": realized_pnl}

@app.post("/api/trade/close-all")
async def close_all_positions(authorized: bool = Depends(verify_auth)):
    """Emergency close all positions"""
    results = []
    
    for symbol, pos in list(trading_data.positions.items()):
        # Use current price or last known price
        current_price = pos.get("current_price", pos["avg_cost"])
        
        request = TradeRequest(
            symbol=symbol,
            quantity=pos["quantity"],
            price=current_price,
            order_type="MARKET"
        )
        
        try:
            result = await sell_stock(request, authorized=True)
            results.append({"symbol": symbol, "status": "closed", "pnl": result.get("pnl", 0)})
        except Exception as e:
            results.append({"symbol": symbol, "status": "error", "error": str(e)})
    
    await manager.broadcast({
        "type": "emergency_close",
        "data": trading_data.get_dashboard_data(),
        "results": results
    })
    
    logger.warning(f"Emergency close executed: {results}")
    
    return {"status": "success", "closed_positions": results}

@app.post("/api/strategy/toggle")
async def toggle_strategy(request: StrategyToggle, authorized: bool = Depends(verify_auth)):
    """Toggle strategy on/off"""
    trading_data.strategy_status["running"] = request.enabled
    trading_data.strategy_status["last_update"] = datetime.now().isoformat()
    
    # Notify bridge
    if bridge_client.connected and bridge_client.ws:
        try:
            await bridge_client.ws.send(json.dumps({
                "action": "toggle_strategy",
                "enabled": request.enabled
            }))
        except Exception as e:
            logger.warning(f"Failed to notify bridge: {e}")
    
    await manager.broadcast({
        "type": "strategy_update",
        "data": trading_data.strategy_status
    })
    
    status = "started" if request.enabled else "stopped"
    logger.info(f"Strategy {status}")
    
    return {"status": "success", "message": f"Strategy {status}"}

# ==================== Z-Score API Endpoints ====================

# Initialize Z-Score strategy
zscore_strategy = ZScoreStrategy()
zscore_trader = ZScoreRealtimeTrader(strategy=zscore_strategy)

@app.get("/api/zscore/{symbol}")
async def get_zscore(symbol: str, authorized: bool = Depends(verify_auth)):
    """
    獲取指定股票的 Z-Score 數據
    
    Args:
        symbol: 股票代碼 (如 TQQQ, SQQQ)
        
    Returns:
        Z-Score 計算結果及交易信號
    """
    try:
        # 獲取最新數據
        signal_data = zscore_trader.check_signal(symbol)
        
        if "error" in signal_data:
            raise HTTPException(status_code=404, detail=signal_data["error"])
        
        return {
            "status": "success",
            "symbol": symbol,
            "data": signal_data
        }
    except Exception as e:
        logger.error(f"Error calculating Z-Score for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/zscore/signal")
async def get_zscore_signal(authorized: bool = Depends(verify_auth)):
    """
    獲取當前 Z-Score 交易信號
    
    Returns:
        所有觀察列表股票的 Z-Score 信號
    """
    try:
        signals = []
        watchlist = ["TQQQ", "SQQQ"]  # 默認觀察列表
        
        for symbol in watchlist:
            signal_data = zscore_trader.check_signal(symbol)
            if "error" not in signal_data:
                signals.append(signal_data)
        
        return {
            "status": "success",
            "count": len(signals),
            "signals": signals
        }
    except Exception as e:
        logger.error(f"Error getting Z-Score signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zscore/strategy/start")
async def start_zscore_strategy(authorized: bool = Depends(verify_auth)):
    """啟動 Z-Score 策略"""
    try:
        # 這裡可以添加策略啟動邏輯
        # 例如：開始定期計算 Z-Score、監控信號等
        
        await manager.broadcast({
            "type": "zscore_strategy_update",
            "data": {
                "status": "running",
                "strategy": "ZScore_MeanReversion",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        logger.info("Z-Score strategy started")
        return {
            "status": "success",
            "message": "Z-Score strategy started",
            "strategy_info": zscore_strategy.get_strategy_info()
        }
    except Exception as e:
        logger.error(f"Error starting Z-Score strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zscore/strategy/stop")
async def stop_zscore_strategy(authorized: bool = Depends(verify_auth)):
    """停止 Z-Score 策略"""
    try:
        await manager.broadcast({
            "type": "zscore_strategy_update",
            "data": {
                "status": "stopped",
                "strategy": "ZScore_MeanReversion",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        logger.info("Z-Score strategy stopped")
        return {
            "status": "success",
            "message": "Z-Score strategy stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping Z-Score strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/zscore/status")
async def get_zscore_status(authorized: bool = Depends(verify_auth)):
    """獲取 Z-Score 策略狀態"""
    return {
        "status": "success",
        "strategy": zscore_strategy.get_strategy_info(),
        "trader": zscore_trader.get_status()
    }

# WebSocket endpoint for Dashboard clients
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send initial data
    await websocket.send_json({
        "type": "initial",
        "data": trading_data.get_dashboard_data()
    })
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("action") == "get_data":
                await websocket.send_json({
                    "type": "data_update",
                    "data": trading_data.get_dashboard_data()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Startup event - connect to bridge
@app.on_event("startup")
async def startup_event():
    """Start bridge client on startup"""
    logger.info("Starting Dashboard (Framework A)...")
    # 使用獨立任務啟動 Bridge 連接，避免阻塞 Dashboard 啟動
    asyncio.create_task(start_bridge_client())

async def start_bridge_client():
    """獨立啟動 Bridge Client，即使失敗也不影響 Dashboard"""
    max_startup_retries = 3
    for attempt in range(max_startup_retries):
        try:
            logger.info(f"Starting bridge client (attempt {attempt + 1}/{max_startup_retries})...")
            await bridge_client.start()
            # 如果 start() 正常返回（不應該發生，因為是無限循環）
            logger.info("Bridge client stopped normally")
            break
        except asyncio.CancelledError:
            logger.info("Bridge client cancelled")
            break
        except Exception as e:
            logger.error(f"Bridge client error: {e}")
            if attempt < max_startup_retries - 1:
                logger.info(f"Retrying bridge client in 5 seconds...")
                await asyncio.sleep(5)
            else:
                logger.warning("⚠️ Bridge client failed to start after all retries")
                logger.info("✅ Dashboard will continue running without bridge connection")
                # 即使 Bridge 連接失敗，Dashboard 也繼續運行
                # 啟動一個虛擬的監控任務，定期檢查是否需要重試連接
                asyncio.create_task(maintain_bridge_connection())

async def maintain_bridge_connection():
    """維護 Bridge 連接，定期嘗試重連"""
    while True:
        if not bridge_client.connected and not bridge_client.running:
            try:
                logger.info("Attempting to restart bridge client...")
                bridge_client.running = True
                asyncio.create_task(bridge_client.connect())
            except Exception as e:
                logger.debug(f"Bridge restart attempt failed: {e}")
        await asyncio.sleep(10)  # 每 10 秒檢查一次

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop bridge client on shutdown"""
    logger.info("Shutting down Dashboard...")
    bridge_client.stop()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DASHBOARD_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
