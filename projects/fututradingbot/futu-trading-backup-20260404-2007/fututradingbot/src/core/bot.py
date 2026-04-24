"""
交易機器人核心類
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime

from src.utils.logger import logger
from src.config.settings import Settings
from src.api.futu_client import FutuAPIClient, Market, TrdEnv


class TradingBot:
    """
    交易機器人主類
    協調各個模塊的工作
    """
    
    def __init__(self, settings: Settings):
        """
        初始化交易機器人
        
        Args:
            settings: 配置對象
        """
        self.settings = settings
        self.api_client: Optional[FutuAPIClient] = None
        self._running = False
        self._start_time: Optional[datetime] = None
        
        logger.info("交易機器人初始化完成")
    
    def start(self):
        """啟動機器人"""
        logger.info("正在啟動交易機器人...")
        
        try:
            # 初始化 API 客戶端
            self.api_client = FutuAPIClient(
                host=self.settings.opend.host,
                port=self.settings.opend.port
            )
            
            # 連接行情
            if not self.api_client.connect_quote():
                raise ConnectionError("無法連接到行情服務")
            
            # 連接交易（配置的市場）
            for market_str in self.settings.trading.markets:
                market = Market[market_str]
                if not self.api_client.connect_trade(market):
                    logger.warning(f"無法連接到 {market_str} 交易服務")
            
            # 解鎖交易（實盤需要）
            if self.settings.trading.env == "REAL":
                self._unlock_trading()
            
            # 啟動行情接收
            if self.api_client.quote_client:
                self.api_client.quote_client.start()
            
            self._running = True
            self._start_time = datetime.now()
            
            logger.info("=" * 50)
            logger.info("交易機器人啟動成功！")
            logger.info(f"交易環境: {self.settings.trading.env}")
            logger.info(f"交易市場: {', '.join(self.settings.trading.markets)}")
            logger.info(f"啟動時間: {self._start_time}")
            logger.info("=" * 50)
            
            # 主循環
            self._main_loop()
            
        except Exception as e:
            logger.exception(f"機器人啟動失敗: {e}")
            self.stop()
            raise
    
    def stop(self):
        """停止機器人"""
        logger.info("正在停止交易機器人...")
        self._running = False
        
        if self.api_client:
            self.api_client.disconnect_all()
        
        run_duration = ""
        if self._start_time:
            duration = datetime.now() - self._start_time
            run_duration = f"運行時長: {duration}"
        
        logger.info(f"交易機器人已停止。{run_duration}")
    
    def _unlock_trading(self):
        """解鎖交易接口"""
        password = self.settings.trading.unlock_password
        if not password:
            logger.warning("未配置交易解鎖密碼，實盤交易可能無法進行")
            return
        
        for market, client in self.api_client.trade_clients.items():
            if client.unlock_trade(password):
                logger.info(f"{market.name} 交易接口解鎖成功")
            else:
                logger.error(f"{market.name} 交易接口解鎖失敗")
    
    def _main_loop(self):
        """主循環"""
        logger.info("進入主循環...")
        
        while self._running:
            try:
                # 這裡可以添加：
                # 1. 策略檢查
                # 2. 訂單狀態監控
                # 3. 風險檢查
                # 4. 數據持久化
                
                # 簡單的心跳日誌
                if int(time.time()) % 60 == 0:  # 每分鐘
                    logger.debug("機器人運行中...")
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("收到中斷信號")
                break
            except Exception as e:
                logger.exception(f"主循環出錯: {e}")
                time.sleep(5)
    
    def get_status(self) -> Dict[str, Any]:
        """
        獲取機器人狀態
        
        Returns:
            狀態字典
        """
        status = {
            "running": self._running,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "environment": self.settings.trading.env,
            "markets": self.settings.trading.markets,
            "quote_connected": self.api_client.quote_client is not None,
            "trade_connected": {
                market.name: client is not None
                for market, client in self.api_client.trade_clients.items()
            } if self.api_client else {}
        }
        return status
