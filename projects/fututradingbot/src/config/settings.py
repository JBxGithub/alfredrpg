"""
配置管理系統
統一管理應用配置
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import yaml
from dotenv import load_dotenv


@dataclass
class OpenDConfig:
    """OpenD 網關配置"""
    host: str = "127.0.0.1"
    port: int = 11111
    timeout: int = 30
    websocket_port: Optional[int] = None


@dataclass
class TradingConfig:
    """交易配置"""
    env: str = "SIMULATE"  # SIMULATE or REAL
    markets: List[str] = field(default_factory=lambda: ["HK"])
    unlock_password: str = ""
    trading_hours: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoggingConfig:
    """日誌配置"""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"
    console_output: bool = True
    file_output: bool = True
    log_dir: str = "logs"
    log_file: str = "trading.log"
    max_size: str = "10MB"
    backup_count: int = 5
    rotation: str = "00:00"
    retention: str = "30 days"


@dataclass
class RiskConfig:
    """風險控制配置"""
    max_position_ratio: float = 0.8
    max_single_order_ratio: float = 0.2
    max_daily_loss_ratio: float = 0.05
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10
    trailing_stop_pct: float = 0.03
    max_open_orders: int = 10
    max_orders_per_minute: int = 5
    price_limit_pct: float = 0.05


@dataclass
class StrategyConfig:
    """策略配置"""
    default_strategy: str = "macd_cross"
    update_interval: int = 60
    subscription: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationConfig:
    """通知配置"""
    enabled: bool = False
    channels: List[Dict[str, Any]] = field(default_factory=list)


class Settings:
    """
    配置管理類
    從 YAML 文件和環境變數加載配置
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路徑，默認為 config/config.yaml
        """
        # 加載環境變數
        load_dotenv()
        
        # 確定配置文件路徑
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)
        
        # 加載 YAML 配置
        self._config = self._load_yaml(config_path)
        
        # 初始化各個配置模塊
        self.opend = self._init_opend_config()
        self.trading = self._init_trading_config()
        self.logging = self._init_logging_config()
        self.risk = self._init_risk_config()
        self.strategy = self._init_strategy_config()
        self.notification = self._init_notification_config()
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """加載 YAML 配置文件"""
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _init_opend_config(self) -> OpenDConfig:
        """初始化 OpenD 配置"""
        opend_data = self._config.get('opend', {})
        return OpenDConfig(
            host=opend_data.get('host', '127.0.0.1'),
            port=opend_data.get('port', 11111),
            timeout=opend_data.get('timeout', 30),
            websocket_port=opend_data.get('websocket_port')
        )
    
    def _init_trading_config(self) -> TradingConfig:
        """初始化交易配置"""
        trading_data = self._config.get('trading', {})
        
        # 從環境變數獲取解鎖密碼
        unlock_password = trading_data.get('unlock_password', '')
        if not unlock_password:
            unlock_password = os.getenv('FUTU_UNLOCK_PASSWORD', '')
        
        return TradingConfig(
            env=trading_data.get('env', 'SIMULATE'),
            markets=trading_data.get('markets', ['HK']),
            unlock_password=unlock_password,
            trading_hours=trading_data.get('trading_hours', {})
        )
    
    def _init_logging_config(self) -> LoggingConfig:
        """初始化日誌配置"""
        logging_data = self._config.get('logging', {})
        return LoggingConfig(
            level=logging_data.get('level', 'INFO'),
            format=logging_data.get('format'),
            console_output=logging_data.get('console_output', True),
            file_output=logging_data.get('file_output', True),
            log_dir=logging_data.get('log_dir', 'logs'),
            log_file=logging_data.get('log_file', 'trading.log'),
            max_size=logging_data.get('max_size', '10MB'),
            backup_count=logging_data.get('backup_count', 5),
            rotation=logging_data.get('rotation', '00:00'),
            retention=logging_data.get('retention', '30 days')
        )
    
    def _init_risk_config(self) -> RiskConfig:
        """初始化風險控制配置"""
        risk_data = self._config.get('risk', {})
        return RiskConfig(
            max_position_ratio=risk_data.get('max_position_ratio', 0.8),
            max_single_order_ratio=risk_data.get('max_single_order_ratio', 0.2),
            max_daily_loss_ratio=risk_data.get('max_daily_loss_ratio', 0.05),
            stop_loss_pct=risk_data.get('stop_loss_pct', 0.05),
            take_profit_pct=risk_data.get('take_profit_pct', 0.10),
            trailing_stop_pct=risk_data.get('trailing_stop_pct', 0.03),
            max_open_orders=risk_data.get('max_open_orders', 10),
            max_orders_per_minute=risk_data.get('max_orders_per_minute', 5),
            price_limit_pct=risk_data.get('price_limit_pct', 0.05)
        )
    
    def _init_strategy_config(self) -> StrategyConfig:
        """初始化策略配置"""
        strategy_data = self._config.get('strategy', {})
        return StrategyConfig(
            default_strategy=strategy_data.get('default_strategy', 'macd_cross'),
            update_interval=strategy_data.get('update_interval', 60),
            subscription=strategy_data.get('subscription', {})
        )
    
    def _init_notification_config(self) -> NotificationConfig:
        """初始化通知配置"""
        notification_data = self._config.get('notification', {})
        return NotificationConfig(
            enabled=notification_data.get('enabled', False),
            channels=notification_data.get('channels', [])
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        獲取原始配置值
        
        Args:
            key: 配置鍵名
            default: 默認值
            
        Returns:
            配置值
        """
        return self._config.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """將配置轉換為字典"""
        return {
            'opend': self.opend.__dict__,
            'trading': self.trading.__dict__,
            'logging': self.logging.__dict__,
            'risk': self.risk.__dict__,
            'strategy': self.strategy.__dict__,
            'notification': self.notification.__dict__
        }
