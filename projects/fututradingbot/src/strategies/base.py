"""
策略基類
定義交易策略的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import logger


class SignalType(Enum):
    """交易信號類型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


@dataclass
class TradeSignal:
    """交易信號"""
    code: str
    signal: SignalType
    price: Optional[float] = None
    qty: Optional[int] = None
    reason: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseStrategy(ABC):
    """
    交易策略基類
    所有策略都應該繼承此類
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        初始化策略
        
        Args:
            name: 策略名稱
            config: 策略配置
        """
        self.name = name
        self.config = config or {}
        self._initialized = False
        
        logger.info(f"策略 '{name}' 已創建")
    
    def initialize(self):
        """初始化策略，子類可以重寫"""
        self._initialized = True
        logger.info(f"策略 '{self.name}' 已初始化")
    
    @abstractmethod
    def on_data(self, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """
        處理行情數據，產生交易信號
        
        Args:
            data: 行情數據
            
        Returns:
            TradeSignal or None: 交易信號
        """
        pass
    
    @abstractmethod
    def on_order_update(self, order: Dict[str, Any]):
        """
        處理訂單更新
        
        Args:
            order: 訂單信息
        """
        pass
    
    @abstractmethod
    def on_position_update(self, position: Dict[str, Any]):
        """
        處理持倉更新
        
        Args:
            position: 持倉信息
        """
        pass
    
    def get_params(self) -> Dict[str, Any]:
        """
        獲取策略參數
        
        Returns:
            參數字典
        """
        return self.config.copy()
    
    def update_params(self, params: Dict[str, Any]):
        """
        更新策略參數
        
        Args:
            params: 新參數
        """
        self.config.update(params)
        logger.info(f"策略 '{self.name}' 參數已更新: {params}")
    
    def reset(self):
        """重置策略狀態"""
        self._initialized = False
        logger.info(f"策略 '{self.name}' 已重置")


class StrategyManager:
    """
    策略管理器
    管理多個策略的運行
    """
    
    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}
        self._active_strategy: Optional[str] = None
        
    def register(self, strategy: BaseStrategy):
        """
        註冊策略
        
        Args:
            strategy: 策略實例
        """
        self._strategies[strategy.name] = strategy
        logger.info(f"策略 '{strategy.name}' 已註冊")
    
    def unregister(self, name: str):
        """
        註銷策略
        
        Args:
            name: 策略名稱
        """
        if name in self._strategies:
            del self._strategies[name]
            logger.info(f"策略 '{name}' 已註銷")
    
    def get(self, name: str) -> Optional[BaseStrategy]:
        """
        獲取策略
        
        Args:
            name: 策略名稱
            
        Returns:
            策略實例或 None
        """
        return self._strategies.get(name)
    
    def set_active(self, name: str):
        """
        設置當前活躍策略
        
        Args:
            name: 策略名稱
        """
        if name not in self._strategies:
            raise ValueError(f"策略 '{name}' 未註冊")
        
        self._active_strategy = name
        logger.info(f"當前活躍策略: '{name}'")
    
    def get_active(self) -> Optional[BaseStrategy]:
        """獲取當前活躍策略"""
        if self._active_strategy:
            return self._strategies.get(self._active_strategy)
        return None
    
    def list_strategies(self) -> List[str]:
        """列出所有已註冊的策略"""
        return list(self._strategies.keys())
    
    def process_data(self, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """
        使用活躍策略處理數據
        
        Args:
            data: 行情數據
            
        Returns:
            交易信號或 None
        """
        strategy = self.get_active()
        if strategy:
            return strategy.on_data(data)
        return None
