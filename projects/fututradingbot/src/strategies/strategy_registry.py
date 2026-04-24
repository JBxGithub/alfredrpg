"""
策略註冊中心 - Strategy Registry

統一策略接口、動態策略加載、策略組合管理

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import os
import sys
import importlib
import inspect
from typing import Dict, List, Optional, Any, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.utils.logger import logger


class StrategyType(Enum):
    """策略類型"""
    TREND_FOLLOWING = "trend_following"      # 趨勢跟隨
    MEAN_REVERSION = "mean_reversion"        # 均值回歸
    BREAKOUT = "breakout"                    # 突破
    MOMENTUM = "momentum"                    # 動量
    PAIRS_TRADING = "pairs_trading"          # 配對交易
    ARBITRAGE = "arbitrage"                  # 套利
    MULTI_FACTOR = "multi_factor"            # 多因子
    ML_BASED = "ml_based"                    # 機器學習


@dataclass
class StrategyMetadata:
    """策略元數據"""
    name: str
    strategy_type: StrategyType
    description: str
    author: str
    version: str
    created_at: datetime
    updated_at: datetime
    parameters: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'strategy_type': self.strategy_type.value,
            'description': self.description,
            'author': self.author,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'parameters': self.parameters,
            'performance_metrics': self.performance_metrics,
            'tags': self.tags
        }


@dataclass
class StrategyInstance:
    """策略實例包裝"""
    metadata: StrategyMetadata
    strategy_class: Type[BaseStrategy]
    instance: Optional[BaseStrategy] = None
    is_active: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    
    def create_instance(self, config: Optional[Dict[str, Any]] = None) -> BaseStrategy:
        """創建策略實例"""
        if config:
            self.config.update(config)
        self.instance = self.strategy_class(config=self.config)
        return self.instance
    
    def activate(self):
        """激活策略"""
        self.is_active = True
        if self.instance:
            self.instance.initialize()
    
    def deactivate(self):
        """停用策略"""
        self.is_active = False


class StrategyRegistry:
    """
    策略註冊中心
    
    管理所有交易策略的註冊、加載和實例化
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._strategies: Dict[str, StrategyInstance] = {}
        self._active_strategies: Dict[str, StrategyInstance] = {}
        self._strategy_paths: List[str] = []
        self._initialized = True
        
        logger.info("策略註冊中心初始化完成")
    
    def register(
        self,
        strategy_class: Type[BaseStrategy],
        name: Optional[str] = None,
        strategy_type: StrategyType = StrategyType.TREND_FOLLOWING,
        description: str = "",
        author: str = "FutuTradingBot",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None
    ) -> StrategyInstance:
        """
        註冊策略
        
        Args:
            strategy_class: 策略類
            name: 策略名稱 (默認使用類名)
            strategy_type: 策略類型
            description: 策略描述
            author: 作者
            version: 版本
            tags: 標籤列表
            
        Returns:
            StrategyInstance: 策略實例包裝
        """
        if name is None:
            name = strategy_class.__name__
        
        if name in self._strategies:
            logger.warning(f"策略 '{name}' 已存在，將被覆蓋")
        
        metadata = StrategyMetadata(
            name=name,
            strategy_type=strategy_type,
            description=description,
            author=author,
            version=version,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=tags or []
        )
        
        instance = StrategyInstance(
            metadata=metadata,
            strategy_class=strategy_class
        )
        
        self._strategies[name] = instance
        logger.info(f"策略 '{name}' 已註冊 (類型: {strategy_type.value})")
        
        return instance
    
    def unregister(self, name: str) -> bool:
        """
        註銷策略
        
        Args:
            name: 策略名稱
            
        Returns:
            bool: 是否成功
        """
        if name not in self._strategies:
            logger.warning(f"策略 '{name}' 不存在")
            return False
        
        # 如果正在運行，先停用
        if name in self._active_strategies:
            self.deactivate(name)
        
        del self._strategies[name]
        logger.info(f"策略 '{name}' 已註銷")
        return True
    
    def get(self, name: str) -> Optional[StrategyInstance]:
        """
        獲取策略實例
        
        Args:
            name: 策略名稱
            
        Returns:
            StrategyInstance or None
        """
        return self._strategies.get(name)
    
    def get_strategy_class(self, name: str) -> Optional[Type[BaseStrategy]]:
        """獲取策略類"""
        instance = self._strategies.get(name)
        return instance.strategy_class if instance else None
    
    def create_strategy(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseStrategy]:
        """
        創建策略實例
        
        Args:
            name: 策略名稱
            config: 配置參數
            
        Returns:
            BaseStrategy or None
        """
        instance = self._strategies.get(name)
        if not instance:
            logger.error(f"策略 '{name}' 未註冊")
            return None
        
        return instance.create_instance(config)
    
    def activate(self, name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        激活策略
        
        Args:
            name: 策略名稱
            config: 配置參數
            
        Returns:
            bool: 是否成功
        """
        instance = self._strategies.get(name)
        if not instance:
            logger.error(f"策略 '{name}' 未註冊")
            return False
        
        if name in self._active_strategies:
            logger.info(f"策略 '{name}' 已經在運行中")
            return True
        
        instance.create_instance(config)
        instance.activate()
        self._active_strategies[name] = instance
        
        logger.info(f"策略 '{name}' 已激活")
        return True
    
    def deactivate(self, name: str) -> bool:
        """
        停用策略
        
        Args:
            name: 策略名稱
            
        Returns:
            bool: 是否成功
        """
        if name not in self._active_strategies:
            logger.warning(f"策略 '{name}' 未在運行中")
            return False
        
        instance = self._active_strategies[name]
        instance.deactivate()
        del self._active_strategies[name]
        
        logger.info(f"策略 '{name}' 已停用")
        return True
    
    def list_strategies(self, strategy_type: Optional[StrategyType] = None) -> List[str]:
        """
        列出所有策略
        
        Args:
            strategy_type: 按類型過濾
            
        Returns:
            策略名稱列表
        """
        if strategy_type:
            return [
                name for name, inst in self._strategies.items()
                if inst.metadata.strategy_type == strategy_type
            ]
        return list(self._strategies.keys())
    
    def list_active_strategies(self) -> List[str]:
        """列出活躍策略"""
        return list(self._active_strategies.keys())
    
    def get_metadata(self, name: str) -> Optional[StrategyMetadata]:
        """獲取策略元數據"""
        instance = self._strategies.get(name)
        return instance.metadata if instance else None
    
    def discover_strategies(self, path: str) -> List[str]:
        """
        發現路徑中的策略
        
        Args:
            path: 策略文件路徑
            
        Returns:
            發現的策略名稱列表
        """
        discovered = []
        
        if not os.path.exists(path):
            logger.warning(f"路徑不存在: {path}")
            return discovered
        
        # 添加到路徑
        if path not in sys.path:
            sys.path.insert(0, path)
            self._strategy_paths.append(path)
        
        # 掃描Python文件
        for filename in os.listdir(path):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(module_name)
                    
                    # 查找策略類
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseStrategy) and 
                            obj != BaseStrategy):
                            
                            # 自動註冊
                            self.register(obj, name=name)
                            discovered.append(name)
                            
                except Exception as e:
                    logger.error(f"加載模組 {module_name} 失敗: {e}")
        
        return discovered
    
    def export_registry(self, filepath: str):
        """
        導出註冊表
        
        Args:
            filepath: 輸出文件路徑
        """
        data = {
            'strategies': {
                name: inst.metadata.to_dict()
                for name, inst in self._strategies.items()
            },
            'active_strategies': list(self._active_strategies.keys()),
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"註冊表已導出: {filepath}")
    
    def import_registry(self, filepath: str):
        """
        導入註冊表
        
        Args:
            filepath: 輸入文件路徑
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"註冊表已導入: {filepath}")
        return data


class StrategyPortfolio:
    """
    策略組合
    
    管理多個策略的組合運行
    """
    
    def __init__(self, name: str, registry: Optional[StrategyRegistry] = None):
        """
        初始化策略組合
        
        Args:
            name: 組合名稱
            registry: 策略註冊中心
        """
        self.name = name
        self.registry = registry or StrategyRegistry()
        self._strategies: Dict[str, Dict[str, Any]] = {}
        self._weights: Dict[str, float] = {}
        self._allocation_method: str = "equal"  # equal, risk_parity, performance
    
    def add_strategy(
        self,
        name: str,
        weight: float = 1.0,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加策略到組合
        
        Args:
            name: 策略名稱
            weight: 權重
            config: 配置參數
            
        Returns:
            bool: 是否成功
        """
        if name not in self.registry.list_strategies():
            logger.error(f"策略 '{name}' 未註冊")
            return False
        
        self._strategies[name] = {
            'config': config or {},
            'instance': None,
            'active': False
        }
        self._weights[name] = weight
        
        logger.info(f"策略 '{name}' 已添加到組合 '{self.name}' (權重: {weight})")
        return True
    
    def remove_strategy(self, name: str) -> bool:
        """從組合中移除策略"""
        if name not in self._strategies:
            return False
        
        self.deactivate_strategy(name)
        del self._strategies[name]
        del self._weights[name]
        
        logger.info(f"策略 '{name}' 已從組合 '{self.name}' 移除")
        return True
    
    def set_weight(self, name: str, weight: float):
        """設置策略權重"""
        if name in self._weights:
            self._weights[name] = weight
            logger.info(f"策略 '{name}' 權重設置為 {weight}")
    
    def activate_strategy(self, name: str) -> bool:
        """激活組合中的策略"""
        if name not in self._strategies:
            return False
        
        strategy_info = self._strategies[name]
        if strategy_info['active']:
            return True
        
        instance = self.registry.create_strategy(name, strategy_info['config'])
        if instance:
            instance.initialize()
            strategy_info['instance'] = instance
            strategy_info['active'] = True
            logger.info(f"組合策略 '{name}' 已激活")
            return True
        
        return False
    
    def deactivate_strategy(self, name: str) -> bool:
        """停用組合中的策略"""
        if name not in self._strategies:
            return False
        
        strategy_info = self._strategies[name]
        strategy_info['active'] = False
        strategy_info['instance'] = None
        
        logger.info(f"組合策略 '{name}' 已停用")
        return True
    
    def activate_all(self):
        """激活所有策略"""
        for name in self._strategies:
            self.activate_strategy(name)
    
    def deactivate_all(self):
        """停用所有策略"""
        for name in self._strategies:
            self.deactivate_strategy(name)
    
    def get_signals(self, data: Dict[str, Any]) -> List[TradeSignal]:
        """
        獲取所有策略的信號
        
        Args:
            data: 市場數據
            
        Returns:
            信號列表
        """
        signals = []
        
        for name, info in self._strategies.items():
            if info['active'] and info['instance']:
                signal = info['instance'].on_data(data)
                if signal:
                    signal.metadata = signal.metadata or {}
                    signal.metadata['strategy'] = name
                    signal.metadata['weight'] = self._weights.get(name, 1.0)
                    signals.append(signal)
        
        return signals
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """獲取組合摘要"""
        return {
            'name': self.name,
            'total_strategies': len(self._strategies),
            'active_strategies': sum(1 for s in self._strategies.values() if s['active']),
            'strategies': list(self._strategies.keys()),
            'weights': self._weights.copy(),
            'allocation_method': self._allocation_method
        }


# 全局註冊中心實例
_registry = None

def get_registry() -> StrategyRegistry:
    """獲取全局策略註冊中心"""
    global _registry
    if _registry is None:
        _registry = StrategyRegistry()
    return _registry


def register_strategy(
    strategy_class: Type[BaseStrategy],
    name: Optional[str] = None,
    strategy_type: StrategyType = StrategyType.TREND_FOLLOWING,
    description: str = "",
    author: str = "FutuTradingBot",
    version: str = "1.0.0",
    tags: Optional[List[str]] = None
) -> StrategyInstance:
    """便捷函數：註冊策略"""
    return get_registry().register(
        strategy_class, name, strategy_type, description, author, version, tags
    )
