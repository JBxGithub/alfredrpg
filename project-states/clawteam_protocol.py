# ClawTeam - Agent 通訊協議實現
# 用於 Agent 間消息傳遞與協調

import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from aiohttp import web

class MessageType(Enum):
    DATA_UPDATE = "data_update"
    TRADING_SIGNAL = "trading_signal"
    TRADE_EXECUTION = "trade_execution"
    COMMAND = "command"
    STATUS = "status"
    ALERT = "alert"
    HEARTBEAT = "heartbeat"

class Priority(Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

@dataclass
class MessageHeader:
    message_id: str
    timestamp: str
    from_agent: str
    to_agent: str
    priority: str
    
    @classmethod
    def create(cls, from_agent: str, to_agent: str, priority: Priority = Priority.NORMAL):
        return cls(
            message_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            from_agent=from_agent,
            to_agent=to_agent,
            priority=priority.value
        )

@dataclass
class Message:
    header: MessageHeader
    body: Dict[str, Any]
    meta: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": asdict(self.header),
            "body": self.body,
            "meta": self.meta
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        header = MessageHeader(**data["header"])
        return cls(header=header, body=data["body"], meta=data["meta"])

class ClawTeamAgent:
    """ClawTeam Agent 基類"""
    
    def __init__(self, agent_id: str, agent_name: str, port: int):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.port = port
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.peers: Dict[str, str] = {}  # agent_id -> endpoint
        
    def register_handler(self, msg_type: MessageType, handler: Callable):
        """註冊消息處理器"""
        self.message_handlers[msg_type] = handler
        
    def add_peer(self, agent_id: str, endpoint: str):
        """添加對等 Agent"""
        self.peers[agent_id] = endpoint
        
    async def send_message(self, to_agent: str, msg_type: MessageType, 
                          payload: Dict[str, Any], priority: Priority = Priority.NORMAL) -> bool:
        """發送消息到指定 Agent"""
        if to_agent not in self.peers:
            print(f"[ERROR] Unknown agent: {to_agent}")
            return False
            
        header = MessageHeader.create(self.agent_id, to_agent, priority)
        message = Message(
            header=header,
            body={
                "type": msg_type.value,
                "payload": payload
            },
            meta={
                "requires_ack": True,
                "ttl_seconds": 300
            }
        )
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.peers[to_agent]}/message",
                    json=message.to_dict(),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"[ERROR] Failed to send message to {to_agent}: {e}")
            return False
    
    async def broadcast(self, msg_type: MessageType, payload: Dict[str, Any],
                       priority: Priority = Priority.NORMAL):
        """廣播消息到所有對等 Agent"""
        tasks = [
            self.send_message(agent_id, msg_type, payload, priority)
            for agent_id in self.peers.keys()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_message(self, request: web.Request) -> web.Response:
        """處理收到的消息"""
        try:
            data = await request.json()
            message = Message.from_dict(data)
            msg_type = MessageType(message.body["type"])
            
            print(f"[{self.agent_name}] Received {msg_type.value} from {message.header.from_agent}")
            
            if msg_type in self.message_handlers:
                await self.message_handlers[msg_type](message)
            else:
                print(f"[WARNING] No handler for {msg_type.value}")
                
            return web.json_response({"status": "ok", "ack": message.header.message_id})
        except Exception as e:
            print(f"[ERROR] Failed to handle message: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=500)
    
    async def health_check(self, request: web.Request) -> web.Response:
        """健康檢查端點"""
        return web.json_response({
            "agent": self.agent_id,
            "name": self.agent_name,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    async def start(self):
        """啟動 Agent 服務"""
        app = web.Application()
        app.router.add_post("/message", self.handle_message)
        app.router.add_get("/health", self.health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.port)
        await site.start()
        
        print(f"[{self.agent_name}] Agent started on port {self.port}")
        
        # 保持運行
        while True:
            await asyncio.sleep(3600)


class DataForgeAgent(ClawTeamAgent):
    """DataForge - 數據工程師 Agent"""
    
    def __init__(self):
        super().__init__("dataforge-001", "DataForge", 8001)
        self.market_data = {}
        
    async def fetch_market_data(self, ticker: str) -> Dict[str, Any]:
        """獲取市場數據"""
        # 這裡整合 Futu API
        data = {
            "ticker": ticker,
            "price": 0.0,
            "volume": 0,
            "indicators": {}
        }
        return data
    
    async def publish_data_update(self, ticker: str):
        """發布數據更新"""
        data = await self.fetch_market_data(ticker)
        await self.broadcast(MessageType.DATA_UPDATE, {
            "ticker": ticker,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })


class SignalForgeAgent(ClawTeamAgent):
    """SignalForge - 信號工程師 Agent"""
    
    def __init__(self):
        super().__init__("signalforge-001", "SignalForge", 8002)
        self.latest_signals = {}
        
    async def generate_signal(self, ticker: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成交易信號"""
        # Z-Score Mean Reversion 策略
        z_score = data.get("indicators", {}).get("z_score", 0)
        rsi = data.get("indicators", {}).get("rsi", 50)
        
        signal = None
        if z_score < -1.65 and rsi < 30:
            signal = {
                "ticker": ticker,
                "action": "BUY",
                "confidence": 0.85,
                "factors": ["z_score_oversold", "rsi_oversold"],
                "params": {"z_score": z_score, "rsi": rsi}
            }
        elif z_score > 1.65 and rsi > 70:
            signal = {
                "ticker": ticker,
                "action": "SELL",
                "confidence": 0.85,
                "factors": ["z_score_overbought", "rsi_overbought"],
                "params": {"z_score": z_score, "rsi": rsi}
            }
        
        return signal
    
    async def on_data_update(self, message: Message):
        """處理數據更新"""
        payload = message.body["payload"]
        ticker = payload["ticker"]
        data = payload["data"]
        
        signal = await self.generate_signal(ticker, data)
        if signal:
            await self.send_message(
                "tradeforge-001",
                MessageType.TRADING_SIGNAL,
                signal,
                Priority.HIGH
            )


class TradeForgeAgent(ClawTeamAgent):
    """TradeForge - 執行工程師 Agent"""
    
    def __init__(self, mode: str = "simulate"):
        super().__init__("tradeforge-001", "TradeForge", 8003)
        self.mode = mode
        self.positions = {}
        self.trade_history = []
        
    async def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """執行交易"""
        trade = {
            "order_id": f"ORD-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "ticker": signal["ticker"],
            "action": signal["action"],
            "quantity": 100,  # 根據倉位管理計算
            "status": "pending"
        }
        
        if self.mode == "simulate":
            trade["status"] = "filled_simulated"
            trade["fill_price"] = 0.0  # 當前市價
        else:
            # 實際調用 Futu API
            pass
        
        self.trade_history.append(trade)
        return trade
    
    async def on_trading_signal(self, message: Message):
        """處理交易信號"""
        signal = message.body["payload"]
        print(f"[TradeForge] Received signal: {signal['action']} {signal['ticker']}")
        
        # 風險檢查
        if not await self.risk_check(signal):
            print("[TradeForge] Risk check failed, rejecting signal")
            return
        
        # 執行交易
        trade = await self.execute_trade(signal)
        
        # 回報結果
        await self.send_message(
            "orchestrator",
            MessageType.TRADE_EXECUTION,
            trade,
            Priority.HIGH
        )
    
    async def risk_check(self, signal: Dict[str, Any]) -> bool:
        """風險檢查"""
        # 檢查倉位限制、日內交易次數等
        return True


class OrchestratorAgent(ClawTeamAgent):
    """中央指揮 Agent - 呀鬼"""
    
    def __init__(self):
        super().__init__("orchestrator", "Alfred (Orchestrator)", 9000)
        self.system_status = {}
        self.agents_health = {}
        
    async def on_trade_execution(self, message: Message):
        """處理交易執行回報"""
        trade = message.body["payload"]
        print(f"[Orchestrator] Trade executed: {trade['order_id']} - {trade['status']}")
        
        # 更新系統狀態
        self.system_status["last_trade"] = trade
        
        # 這裡可以發送 WhatsApp 通知
    
    async def on_alert(self, message: Message):
        """處理警報"""
        alert = message.body["payload"]
        print(f"[Orchestrator] ALERT: {alert['level']} - {alert['message']}")
        
        # 緊急警報通知主人
        if alert.get("level") == "critical":
            pass  # 發送 WhatsApp 緊急通知
    
    async def health_monitor(self):
        """健康監控循環"""
        while True:
            for agent_id, endpoint in self.peers.items():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{endpoint}/health", timeout=5) as resp:
                            if resp.status == 200:
                                self.agents_health[agent_id] = "healthy"
                            else:
                                self.agents_health[agent_id] = "unhealthy"
                except:
                    self.agents_health[agent_id] = "offline"
            
            await asyncio.sleep(30)  # 每 30 秒檢查一次
    
    async def start(self):
        """啟動指揮系統"""
        # 添加對等 Agent
        self.add_peer("dataforge-001", "http://localhost:8001")
        self.add_peer("signalforge-001", "http://localhost:8002")
        self.add_peer("tradeforge-001", "http://localhost:8003")
        
        # 啟動健康監控
        asyncio.create_task(self.health_monitor())
        
        await super().start()


# 使用示例
async def main():
    """啟動整個 ClawTeam 系統"""
    
    # 創建各 Agent
    dataforge = DataForgeAgent()
    signalforge = SignalForgeAgent()
    tradeforge = TradeForgeAgent(mode="simulate")
    orchestrator = OrchestratorAgent()
    
    # 註冊消息處理器
    signalforge.register_handler(MessageType.DATA_UPDATE, signalforge.on_data_update)
    tradeforge.register_handler(MessageType.TRADING_SIGNAL, tradeforge.on_trading_signal)
    orchestrator.register_handler(MessageType.TRADE_EXECUTION, orchestrator.on_trade_execution)
    orchestrator.register_handler(MessageType.ALERT, orchestrator.on_alert)
    
    # 啟動所有 Agent
    await asyncio.gather(
        dataforge.start(),
        signalforge.start(),
        tradeforge.start(),
        orchestrator.start()
    )


if __name__ == "__main__":
    asyncio.run(main())
