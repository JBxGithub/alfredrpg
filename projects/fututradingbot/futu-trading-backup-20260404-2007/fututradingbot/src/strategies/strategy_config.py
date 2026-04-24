"""
策略配置模組
Strategy Configuration Module

提供策略配置加載、驗證和管理功能
"""

import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

from src.utils.logger import logger


class StrategyType(Enum):
    """策略類型"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    ARBITRAGE = "arbitrage"


@dataclass
class TrendStrategyConfig:
    """趨勢策略配置"""
    # 趨勢判斷參數
    ema_fast: int = 12
    ema_slow: int = 26
    ema_trend: int = 60
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    boll_period: int = 20
    boll_std: float = 2.0
    
    # 進場條件
    min_analysis_score: float = 70.0
    min_indicator_resonance: int = 3
    volume_threshold: float = 1.5
    rsi_lower: float = 30.0
    rsi_upper: float = 70.0
    
    # 出場條件
    take_profit_pct: float = 0.05
    stop_loss_pct: float = 0.03
    atr_multiplier_sl: float = 2.0
    atr_multiplier_tp: float = 3.0
    use_atr_stop: bool = False
    trailing_stop: bool = False
    trailing_stop_pct: float = 0.02
    
    # 倉位管理
    fixed_position_pct: float = 0.02
    max_position_value: float = 100000.0
    max_positions: int = 10
    use_kelly: bool = False
    kelly_fraction: float = 0.25
    
    # 時間框架
    timeframes: list = field(default_factory=lambda: ['15m', '1h', '1d'])
    primary_tf: str = '1h'
    
    # 風險控制
    max_daily_trades: int = 5
    cooldown_periods: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'TrendStrategyConfig':
        """從字典創建配置"""
        # 過濾掉無效的鍵
        valid_keys = {k for k in cls.__dataclass_fields__.keys()}
        filtered_config = {k: v for k, v in config.items() if k in valid_keys}
        return cls(**filtered_config)


@dataclass
class RiskManagementConfig:
    """風險管理配置"""
    enabled: bool = True
    max_position_value: float = 1000000.0
    max_order_value: float = 100000.0
    max_daily_loss: float = 50000.0
    max_drawdown_percent: float = 10.0
    max_sector_exposure: float = 0.3
    max_single_stock_exposure: float = 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'RiskManagementConfig':
        valid_keys = {k for k in cls.__dataclass_fields__.keys()}
        filtered_config = {k: v for k, v in config.items() if k in valid_keys}
        return cls(**filtered_config)


@dataclass
class ZScoreStrategyConfig:
    """Z-Score Mean Reversion 策略配置（2026-03-29 最終版）"""
    # Z-Score 參數
    entry_zscore: float = 1.65          # 進場閾值
    exit_zscore: float = 0.5            # 出場閾值（回歸）
    stop_loss_zscore: float = 3.5       # 止損閾值
    lookback_period: int = 60           # 回望期（日）

    # RSI 參數
    rsi_period: int = 14                # RSI 週期
    rsi_overbought: float = 70.0        # 超買閾值
    rsi_oversold: float = 30.0          # 超賣閾值

    # 成交量參數
    volume_ma_period: int = 20          # 成交量均線週期
    volume_threshold: float = 0.5       # 成交量 > 均量 × 50%

    # 止盈止損
    take_profit_pct: float = 0.05       # 止盈 5%
    stop_loss_pct: float = 0.03         # 止損 3%
    time_stop_days: int = 7             # 時間止損 7天

    # 倉位管理
    position_pct: float = 0.50          # 單筆倉位 50%
    max_positions: int = 2              # 最大同時持倉數

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'ZScoreStrategyConfig':
        valid_keys = {k for k in cls.__dataclass_fields__.keys()}
        filtered_config = {k: v for k, v in config.items() if k in valid_keys}
        return cls(**filtered_config)


@dataclass
class BacktestConfig:
    """回測配置"""
    start_date: str = "2023-01-01"
    end_date: str = "2026-01-01"
    initial_capital: float = 100000.0   # 修正為 $100,000
    commission_rate: float = 0.001
    slippage: float = 0.001
    benchmark: str = "TQQQ"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'BacktestConfig':
        valid_keys = {k for k in cls.__dataclass_fields__.keys()}
        filtered_config = {k: v for k, v in config.items() if k in valid_keys}
        return cls(**filtered_config)


class StrategyConfigManager:
    """
    策略配置管理器

    管理所有策略相關配置
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路徑
        """
        self.config_path = config_path or "config/strategy_config.yaml"
        self.trend_config = TrendStrategyConfig()
        self.zscore_config = ZScoreStrategyConfig()  # 添加 Z-Score 配置
        self.risk_config = RiskManagementConfig()
        self.backtest_config = BacktestConfig()

        # 加載配置
        self._load_config()
    
    def _load_config(self):
        """加載配置文件"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {self.config_path}，使用默認配置")
            self._create_default_config()
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'trend_strategy' in config:
                self.trend_config = TrendStrategyConfig.from_dict(config['trend_strategy'])

            if 'zscore_strategy' in config:
                self.zscore_config = ZScoreStrategyConfig.from_dict(config['zscore_strategy'])

            if 'risk_management' in config:
                self.risk_config = RiskManagementConfig.from_dict(config['risk_management'])

            if 'backtest' in config:
                self.backtest_config = BacktestConfig.from_dict(config['backtest'])

            logger.info(f"策略配置已加載: {self.config_path}")
            
        except Exception as e:
            logger.error(f"加載配置文件失敗: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """創建默認配置文件"""
        config = {
            'trend_strategy': self.trend_config.to_dict(),
            'zscore_strategy': self.zscore_config.to_dict(),  # 添加 Z-Score 配置
            'risk_management': self.risk_config.to_dict(),
            'backtest': self.backtest_config.to_dict()
        }
        
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
            logger.info(f"默認配置文件已創建: {self.config_path}")
            
        except Exception as e:
            logger.error(f"創建默認配置文件失敗: {e}")
    
    def save_config(self):
        """保存配置到文件"""
        config = {
            'trend_strategy': self.trend_config.to_dict(),
            'zscore_strategy': self.zscore_config.to_dict(),  # 添加 Z-Score 配置
            'risk_management': self.risk_config.to_dict(),
            'backtest': self.backtest_config.to_dict()
        }
        
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
            logger.info(f"配置已保存: {self.config_path}")
            
        except Exception as e:
            logger.error(f"保存配置失敗: {e}")
    
    def get_trend_strategy_config(self) -> Dict[str, Any]:
        """獲取趨勢策略配置"""
        return self.trend_config.to_dict()
    
    def get_risk_config(self) -> Dict[str, Any]:
        """獲取風險管理配置"""
        return self.risk_config.to_dict()
    
    def get_backtest_config(self) -> Dict[str, Any]:
        """獲取回測配置"""
        return self.backtest_config.to_dict()
    
    def update_trend_config(self, **kwargs):
        """更新趨勢策略配置"""
        for key, value in kwargs.items():
            if hasattr(self.trend_config, key):
                setattr(self.trend_config, key, value)
        self.save_config()
    
    def update_risk_config(self, **kwargs):
        """更新風險管理配置"""
        for key, value in kwargs.items():
            if hasattr(self.risk_config, key):
                setattr(self.risk_config, key, value)
        self.save_config()
    
    def update_backtest_config(self, **kwargs):
        """更新回測配置"""
        for key, value in kwargs.items():
            if hasattr(self.backtest_config, key):
                setattr(self.backtest_config, key, value)
        self.save_config()
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """
        驗證配置有效性
        
        Returns:
            (是否有效, 錯誤信息列表)
        """
        errors = []
        
        # 驗證趨勢策略配置
        tc = self.trend_config
        
        if tc.ema_fast >= tc.ema_slow:
            errors.append("EMA快線週期必須小於慢線週期")
        
        if tc.macd_fast >= tc.macd_slow:
            errors.append("MACD快線週期必須小於慢線週期")
        
        if tc.min_analysis_score < 0 or tc.min_analysis_score > 100:
            errors.append("分析評分閾值必須在0-100之間")
        
        if tc.take_profit_pct <= tc.stop_loss_pct:
            errors.append("止盈比例必須大於止損比例")
        
        if tc.fixed_position_pct <= 0 or tc.fixed_position_pct > 1:
            errors.append("倉位比例必須在0-1之間")
        
        if tc.max_positions <= 0:
            errors.append("最大持倉數量必須大於0")
        
        # 驗證風險管理配置
        rc = self.risk_config
        
        if rc.max_daily_loss <= 0:
            errors.append("每日最大虧損必須大於0")
        
        if rc.max_drawdown_percent <= 0 or rc.max_drawdown_percent > 100:
            errors.append("最大回撤百分比必須在0-100之間")
        
        return len(errors) == 0, errors
    
    def export_to_json(self, filepath: str):
        """導出配置為JSON"""
        config = {
            'trend_strategy': self.trend_config.to_dict(),
            'risk_management': self.risk_config.to_dict(),
            'backtest': self.backtest_config.to_dict()
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已導出: {filepath}")
        except Exception as e:
            logger.error(f"導出配置失敗: {e}")
    
    def import_from_json(self, filepath: str):
        """從JSON導入配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'trend_strategy' in config:
                self.trend_config = TrendStrategyConfig.from_dict(config['trend_strategy'])
            
            if 'risk_management' in config:
                self.risk_config = RiskManagementConfig.from_dict(config['risk_management'])
            
            if 'backtest' in config:
                self.backtest_config = BacktestConfig.from_dict(config['backtest'])
            
            self.save_config()
            logger.info(f"配置已導入: {filepath}")
            
        except Exception as e:
            logger.error(f"導入配置失敗: {e}")


# 全局配置管理器實例
_config_manager: Optional[StrategyConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> StrategyConfigManager:
    """
    獲取全局配置管理器實例
    
    Args:
        config_path: 配置文件路徑
        
    Returns:
        StrategyConfigManager實例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = StrategyConfigManager(config_path)
    return _config_manager
