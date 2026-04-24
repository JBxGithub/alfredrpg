"""
富途 API 連接模組
封裝行情和交易接口
"""

from typing import Optional, List, Dict, Any, Callable
from enum import Enum

import futu as ft

from src.utils.logger import logger


class Market(Enum):
    """市場代碼"""
    HK = ft.Market.HK
    US = ft.Market.US
    SH = ft.Market.SH
    SZ = ft.Market.SZ


class SubType(Enum):
    """訂閱類型"""
    QUOTE = ft.SubType.QUOTE
    TICKER = ft.SubType.TICKER
    K_DAY = ft.SubType.K_DAY
    K_1M = ft.SubType.K_1M
    K_5M = ft.SubType.K_5M
    K_15M = ft.SubType.K_15M
    K_30M = ft.SubType.K_30M
    K_60M = ft.SubType.K_60M
    ORDER_BOOK = ft.SubType.ORDER_BOOK
    RT_DATA = ft.SubType.RT_DATA
    BROKER = ft.SubType.BROKER


class TrdEnv(Enum):
    """交易環境"""
    SIMULATE = ft.TrdEnv.SIMULATE
    REAL = ft.TrdEnv.REAL


class TrdSide(Enum):
    """交易方向"""
    BUY = ft.TrdSide.BUY
    SELL = ft.TrdSide.SELL


class OrderType(Enum):
    """訂單類型"""
    NORMAL = ft.OrderType.NORMAL
    MARKET = ft.OrderType.MARKET
    ABSOLUTE_LIMIT = ft.OrderType.ABSOLUTE_LIMIT


class FutuQuoteClient:
    """
    富途行情客戶端
    封裝行情相關接口
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        """
        初始化行情客戶端
        
        Args:
            host: OpenD 主機地址
            port: OpenD 端口
        """
        self.host = host
        self.port = port
        self._ctx: Optional[ft.OpenQuoteContext] = None
        self._handlers: List[ft.HandlerBase] = []
        
    def connect(self) -> bool:
        """
        連接到 OpenD
        
        Returns:
            bool: 是否連接成功
        """
        try:
            self._ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
            logger.info(f"行情客戶端已連接到 {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"行情客戶端連接失敗: {e}")
            return False
    
    def start(self):
        """開啟異步數據接收"""
        if self._ctx:
            self._ctx.start()
            logger.info("行情異步接收已啟動")
    
    def stop(self):
        """停止異步數據接收"""
        if self._ctx:
            self._ctx.stop()
            logger.info("行情異步接收已停止")
    
    def close(self):
        """關閉連接"""
        if self._ctx:
            self._ctx.close()
            self._ctx = None
            logger.info("行情客戶端已關閉")
    
    def set_handler(self, handler: ft.HandlerBase):
        """
        設置數據回調處理器
        
        Args:
            handler: 回調處理器實例
        """
        if self._ctx:
            self._ctx.set_handler(handler)
            self._handlers.append(handler)
            logger.debug(f"已設置回調處理器: {type(handler).__name__}")
    
    def subscribe(self, code_list: List[str], sub_types: List[SubType]) -> tuple:
        """
        訂閱行情數據
        
        Args:
            code_list: 股票代碼列表，如 ['HK.00700', 'US.AAPL']
            sub_types: 訂閱類型列表
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            logger.error("行情客戶端未連接")
            return -1, None
        
        sub_type_values = [st.value for st in sub_types]
        ret_code, ret_data = self._ctx.subscribe(code_list, sub_type_values)
        
        if ret_code == 0:
            logger.info(f"成功訂閱 {len(code_list)} 個代碼的 {len(sub_types)} 種數據")
        else:
            logger.error(f"訂閱失敗: {ret_data}")
        
        return ret_code, ret_data
    
    def unsubscribe(self, code_list: List[str], sub_types: List[SubType]) -> tuple:
        """
        取消訂閱
        
        Args:
            code_list: 股票代碼列表
            sub_types: 訂閱類型列表
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        
        sub_type_values = [st.value for st in sub_types]
        return self._ctx.unsubscribe(code_list, sub_type_values)
    
    def unsubscribe_all(self) -> tuple:
        """取消所有訂閱"""
        if not self._ctx:
            return -1, None
        return self._ctx.unsubscribe_all()
    
    def get_trading_days(self, market: Market, start: str = None, end: str = None) -> tuple:
        """
        獲取交易日
        
        Args:
            market: 市場
            start: 開始日期 (YYYY-MM-DD)
            end: 結束日期 (YYYY-MM-DD)
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        return self._ctx.get_trading_days(market.value, start, end)
    
    def get_stock_basicinfo(self, market: Market, stock_type: ft.SecurityType = ft.SecurityType.STOCK) -> tuple:
        """
        獲取股票基本信息
        
        Args:
            market: 市場
            stock_type: 股票類型
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        return self._ctx.get_stock_basicinfo(market.value, stock_type)
    
    def get_market_snapshot(self, code_list: List[str]) -> tuple:
        """
        獲取市場快照
        
        Args:
            code_list: 股票代碼列表
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        return self._ctx.get_market_snapshot(code_list)
    
    def get_stock_quote(self, code_list: List[str]) -> tuple:
        """
        獲取報價
        
        Args:
            code_list: 股票代碼列表
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        return self._ctx.get_stock_quote(code_list)
    
    def get_cur_kline(self, code: str, num: int = 100, ktype: ft.KLType = ft.KLType.K_DAY) -> tuple:
        """
        獲取K線數據
        
        Args:
            code: 股票代碼
            num: 獲取數量
            ktype: K線類型
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        return self._ctx.get_cur_kline(code, num, ktype)
    
    def get_order_book(self, code: str) -> tuple:
        """
        獲取買賣盤
        
        Args:
            code: 股票代碼
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        return self._ctx.get_order_book(code)


class FutuTradeClient:
    """
    富途交易客戶端
    封裝交易相關接口
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11111, market: Market = Market.HK):
        """
        初始化交易客戶端
        
        Args:
            host: OpenD 主機地址
            port: OpenD 端口
            market: 市場
        """
        self.host = host
        self.port = port
        self.market = market
        self._ctx = None
        self._is_unlocked = False
        
    def connect(self) -> bool:
        """
        連接到 OpenD
        
        Returns:
            bool: 是否連接成功
        """
        try:
            # Use OpenSecTradeContext for better account support
            self._ctx = ft.OpenSecTradeContext(host=self.host, port=self.port)
            logger.info(f"交易客戶端已連接 (OpenSecTradeContext)")
            return True
        except Exception as e:
            logger.error(f"交易客戶端連接失敗: {e}")
            return False
    
    def close(self):
        """關閉連接"""
        if self._ctx:
            self._ctx.close()
            self._ctx = None
            logger.info(f"{self.market.name} 交易客戶端已關閉")
    
    def unlock_trade(self, password: str) -> bool:
        """
        解鎖交易接口
        
        Args:
            password: 解鎖密碼
            
        Returns:
            bool: 是否解鎖成功
        """
        if not self._ctx:
            logger.error("交易客戶端未連接")
            return False
        
        ret_code, ret_data = self._ctx.unlock_trade(password)
        
        if ret_code == 0:
            self._is_unlocked = True
            logger.info("交易接口解鎖成功")
            return True
        else:
            logger.error(f"交易接口解鎖失敗: {ret_data}")
            return False
    
    def is_unlocked(self) -> bool:
        """檢查是否已解鎖"""
        return self._is_unlocked
    
    def accinfo_query(self, trd_env: TrdEnv = TrdEnv.SIMULATE, acc_id: int = None) -> tuple:
        """
        查詢賬戶資金
        
        Args:
            trd_env: 交易環境
            acc_id: 賬戶 ID（可選）
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        kwargs = {"trd_env": trd_env.value}
        if acc_id is not None:
            kwargs["acc_id"] = acc_id
        return self._ctx.accinfo_query(**kwargs)
    
    def position_list_query(self, trd_env: TrdEnv = TrdEnv.SIMULATE, acc_id: int = None) -> tuple:
        """
        查詢持倉列表
        
        Args:
            trd_env: 交易環境
            acc_id: 賬戶 ID（可選）
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        kwargs = {"trd_env": trd_env.value}
        if acc_id is not None:
            kwargs["acc_id"] = acc_id
        return self._ctx.position_list_query(**kwargs)
    
    def order_list_query(self, trd_env: TrdEnv = TrdEnv.SIMULATE, acc_id: int = None) -> tuple:
        """
        查詢訂單列表
        
        Args:
            trd_env: 交易環境
            acc_id: 賬戶 ID（可選）
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        kwargs = {"trd_env": trd_env.value}
        if acc_id is not None:
            kwargs["acc_id"] = acc_id
        return self._ctx.order_list_query(**kwargs)
    
    def place_order(
        self,
        price: float,
        qty: int,
        code: str,
        trd_side: TrdSide,
        order_type: OrderType = OrderType.NORMAL,
        trd_env: TrdEnv = TrdEnv.SIMULATE
    ) -> tuple:
        """
        下單
        
        Args:
            price: 價格
            qty: 數量
            code: 股票代碼
            trd_side: 交易方向
            order_type: 訂單類型
            trd_env: 交易環境
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        
        if trd_env == TrdEnv.REAL and not self._is_unlocked:
            logger.error("實盤交易前需要先解鎖交易接口")
            return -1, None
        
        ret_code, ret_data = self._ctx.place_order(
            price=price,
            qty=qty,
            code=code,
            trd_side=trd_side.value,
            order_type=order_type.value,
            trd_env=trd_env.value
        )
        
        if ret_code == 0:
            logger.info(f"下單成功: {code} {trd_side.name} {qty}@{price}")
        else:
            logger.error(f"下單失敗: {ret_data}")
        
        return ret_code, ret_data
    
    def cancel_order(self, order_id: str, trd_env: TrdEnv = TrdEnv.SIMULATE) -> tuple:
        """
        撤單
        
        Args:
            order_id: 訂單ID
            trd_env: 交易環境
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        
        ret_code, ret_data = self._ctx.cancel_order(order_id, trd_env=trd_env.value)
        
        if ret_code == 0:
            logger.info(f"撤單成功: {order_id}")
        else:
            logger.error(f"撤單失敗: {ret_data}")
        
        return ret_code, ret_data
    
    def modify_order(
        self,
        order_id: str,
        price: float,
        qty: int,
        trd_env: TrdEnv = TrdEnv.SIMULATE
    ) -> tuple:
        """
        修改訂單
        
        Args:
            order_id: 訂單ID
            price: 新價格
            qty: 新數量
            trd_env: 交易環境
            
        Returns:
            tuple: (ret_code, ret_data)
        """
        if not self._ctx:
            return -1, None
        
        ret_code, ret_data = self._ctx.modify_order(
            order_id=order_id,
            price=price,
            qty=qty,
            trd_env=trd_env.value
        )
        
        if ret_code == 0:
            logger.info(f"改單成功: {order_id} -> {qty}@{price}")
        else:
            logger.error(f"改單失敗: {ret_data}")
        
        return ret_code, ret_data


class FutuAPIClient:
    """
    富途 API 客戶端管理器
    統一管理行情和交易客戶端
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        """
        初始化 API 客戶端
        
        Args:
            host: OpenD 主機地址
            port: OpenD 端口
        """
        self.host = host
        self.port = port
        self.quote_client: Optional[FutuQuoteClient] = None
        self.trade_clients: Dict[Market, FutuTradeClient] = {}
        
    def connect_quote(self) -> bool:
        """
        連接行情客戶端
        
        Returns:
            bool: 是否連接成功
        """
        self.quote_client = FutuQuoteClient(self.host, self.port)
        return self.quote_client.connect()
    
    def connect_trade(self, market: Market) -> bool:
        """
        連接交易客戶端
        
        Args:
            market: 市場
            
        Returns:
            bool: 是否連接成功
        """
        client = FutuTradeClient(self.host, self.port, market)
        if client.connect():
            self.trade_clients[market] = client
            return True
        return False
    
    def disconnect_all(self):
        """斷開所有連接"""
        if self.quote_client:
            self.quote_client.close()
            self.quote_client = None
        
        for client in self.trade_clients.values():
            client.close()
        self.trade_clients.clear()
        
        logger.info("所有 API 連接已關閉")
    
    def get_quote_client(self) -> Optional[FutuQuoteClient]:
        """獲取行情客戶端"""
        return self.quote_client
    
    def get_trade_client(self, market: Market) -> Optional[FutuTradeClient]:
        """獲取交易客戶端"""
        return self.trade_clients.get(market)
