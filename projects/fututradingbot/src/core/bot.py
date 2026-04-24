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
        """主循環 - 整合策略執行和風險管理"""
        logger.info("進入主循環...")
        
        # 初始化風險感知引擎
        from src.core.risk_aware_engine import RiskAwareTradingEngine
        self.trading_engine = RiskAwareTradingEngine(self.settings)
        self.trading_engine.start()
        
        # 初始化策略（從配置加載）
        self._init_strategies()
        
        last_heartbeat = 0
        
        while self._running:
            try:
                current_time = time.time()
                
                # 1. 策略檢查（每5秒）
                if int(current_time) % 5 == 0:
                    self._check_strategies()
                
                # 2. 訂單狀態監控（每10秒）
                if int(current_time) % 10 == 0:
                    self._monitor_orders()
                
                # 3. 風險檢查（每30秒）
                if int(current_time) % 30 == 0:
                    self._check_risk()
                
                # 4. 數據持久化（每分鐘）
                if int(current_time) % 60 == 0:
                    self._persist_data()
                    
                # 心跳日誌（每分鐘）
                if int(current_time) - last_heartbeat >= 60:
                    logger.info(f"機器人運行中... 策略數: {len(self.strategies)}, "
                               f"持倉數: {len(self.trading_engine.risk_manager.positions)}")
                    last_heartbeat = int(current_time)
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("收到中斷信號")
                break
            except Exception as e:
                logger.exception(f"主循環出錯: {e}")
                time.sleep(5)
        
        # 停止交易引擎
        if hasattr(self, 'trading_engine'):
            self.trading_engine.stop()
    
    def _init_strategies(self):
        """初始化策略"""
        self.strategies = []
        
        # 從配置加載策略
        strategy_configs = self.settings.trading.get('strategies', [])
        
        for config in strategy_configs:
            strategy_name = config.get('name')
            strategy_params = config.get('params', {})
            
            try:
                if strategy_name == 'TQQQLongShort':
                    from src.strategies.tqqq_long_short import TQQQLongShortStrategy
                    strategy = TQQQLongShortStrategy(strategy_params)
                elif strategy_name == 'TrendFollowing':
                    from src.strategies.trend_strategy import TrendStrategy
                    strategy = TrendStrategy(strategy_params)
                elif strategy_name == 'ZScore':
                    from src.strategies.zscore_strategy import ZScoreStrategy
                    strategy = ZScoreStrategy(**strategy_params)
                else:
                    logger.warning(f"未知策略: {strategy_name}")
                    continue
                
                strategy.initialize()
                self.strategies.append(strategy)
                logger.info(f"策略初始化成功: {strategy_name}")
                
            except Exception as e:
                logger.error(f"策略初始化失敗 {strategy_name}: {e}")
    
    def _check_strategies(self):
        """檢查策略信號"""
        if not hasattr(self, 'strategies') or not self.strategies:
            return
        
        for strategy in self.strategies:
            try:
                # 獲取策略關注的股票
                symbols = strategy.get_symbols() if hasattr(strategy, 'get_symbols') else ['TQQQ']
                
                for symbol in symbols:
                    # 獲取實時數據
                    data = self._get_market_data(symbol)
                    if data is None:
                        continue
                    
                    # 調用策略分析
                    signal = strategy.on_data(data)
                    
                    if signal:
                        # 風險檢查後執行
                        self._execute_signal(signal)
                        
            except Exception as e:
                logger.error(f"策略檢查出錯: {e}")
    
    def _get_market_data(self, symbol: str) -> Optional[Dict]:
        """獲取市場數據"""
        try:
            if self.api_client and self.api_client.quote_client:
                # 獲取K線數據
                df = self.api_client.get_kl_data(symbol)
                if df is not None and not df.empty:
                    return {'symbol': symbol, 'df': df}
        except Exception as e:
            logger.error(f"獲取市場數據失敗 {symbol}: {e}")
        return None
    
    def _execute_signal(self, signal):
        """執行交易信號"""
        try:
            if not hasattr(self, 'trading_engine'):
                logger.error("交易引擎未初始化")
                return
            
            # 風險檢查
            can_trade, reason = self.trading_engine.check_trade(
                symbol=signal.symbol,
                quantity=signal.qty,
                price=signal.price,
                side='buy' if signal.signal == 'buy' else 'sell'
            )
            
            if not can_trade:
                logger.warning(f"交易被拒絕: {reason}")
                return
            
            # 執行交易
            order_id = self.api_client.place_order(
                symbol=signal.symbol,
                qty=signal.qty,
                price=signal.price,
                side=signal.signal
            )
            
            if order_id:
                logger.info(f"訂單已提交: {order_id}")
                self.trading_engine.record_trade(
                    symbol=signal.symbol,
                    quantity=signal.qty,
                    price=signal.price,
                    side=signal.signal,
                    order_id=order_id
                )
            
        except Exception as e:
            logger.error(f"執行信號失敗: {e}")
    
    def _monitor_orders(self):
        """監控訂單狀態"""
        try:
            if self.api_client:
                orders = self.api_client.get_order_list()
                # 更新訂單狀態
                for order in orders:
                    if hasattr(self, 'trading_engine'):
                        self.trading_engine.update_order_status(order)
        except Exception as e:
            logger.error(f"監控訂單失敗: {e}")
    
    def _check_risk(self):
        """檢查風險狀態"""
        try:
            if hasattr(self, 'trading_engine'):
                # 更新賬戶信息
                account = self.api_client.get_account_info()
                if account:
                    self.trading_engine.update_account_info(
                        total_capital=account.get('total_assets', 0),
                        margin_used=account.get('margin_used', 0),
                        margin_available=account.get('available_cash', 0)
                    )
                
                # 更新持倉信息
                positions = self.api_client.get_position_list()
                self.trading_engine.update_positions(positions)
                
        except Exception as e:
            logger.error(f"風險檢查失敗: {e}")
    
    def _persist_data(self):
        """持久化數據"""
        try:
            # 保存交易記錄
            if hasattr(self, 'trading_engine'):
                self.trading_engine.save_trade_history()
            
            # 保存策略狀態
            for strategy in getattr(self, 'strategies', []):
                if hasattr(strategy, 'save_state'):
                    strategy.save_state()
                    
        except Exception as e:
            logger.error(f"數據持久化失敗: {e}")
    
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
