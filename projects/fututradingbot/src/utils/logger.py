"""
Futu Trading Bot - Logging System
富途交易機器人日誌系統

Usage:
    from src.utils.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Application started")
    logger.error("An error occurred", exc_info=True)
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger as _logger
import yaml

# Default configuration
DEFAULT_CONFIG = {
    "logging": {
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        "file": {
            "enabled": True,
            "path": "./logs",
            "filename": "futu_trading_{time:YYYYMMDD}.log",
            "rotation": "1 day",
            "retention": "30 days",
            "compression": "zip"
        },
        "console": {
            "enabled": True,
            "colorize": True
        },
        "error_file": {
            "enabled": True,
            "filename": "futu_trading_errors_{time:YYYYMMDD}.log"
        }
    }
}


class LoggerConfig:
    """Logger configuration manager"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LoggerConfig._initialized:
            return
        
        self.config = self._load_config()
        self._setup_logger()
        LoggerConfig._initialized = True
    
    def _load_config(self) -> dict:
        """Load configuration from config.yaml"""
        config_paths = [
            Path("config/config.yaml"),
            Path("../config/config.yaml"),
            Path("../../config/config.yaml"),
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        if config and 'logging' in config:
                            return config
                except Exception as e:
                    print(f"Warning: Failed to load config from {config_path}: {e}")
        
        return DEFAULT_CONFIG
    
    def _setup_logger(self):
        """Setup loguru logger with configuration"""
        log_config = self.config.get('logging', DEFAULT_CONFIG['logging'])
        
        # Remove default handler
        _logger.remove()
        
        # Console handler
        if log_config.get('console', {}).get('enabled', True):
            _logger.add(
                sys.stdout,
                format=log_config.get('format', DEFAULT_CONFIG['logging']['format']),
                level=log_config.get('level', 'INFO'),
                colorize=log_config.get('console', {}).get('colorize', True),
                enqueue=True
            )
        
        # File handler
        if log_config.get('file', {}).get('enabled', True):
            log_path = Path(log_config.get('file', {}).get('path', './logs'))
            log_path.mkdir(parents=True, exist_ok=True)
            
            filename = log_config.get('file', {}).get('filename', 'futu_trading_{time:YYYYMMDD}.log')
            log_file = log_path / filename
            
            _logger.add(
                str(log_file),
                format=log_config.get('format', DEFAULT_CONFIG['logging']['format']),
                level=log_config.get('level', 'INFO'),
                rotation=log_config.get('file', {}).get('rotation', '1 day'),
                retention=log_config.get('file', {}).get('retention', '30 days'),
                compression=log_config.get('file', {}).get('compression', 'zip'),
                enqueue=True,
                encoding='utf-8'
            )
        
        # Error file handler (separate file for errors)
        if log_config.get('error_file', {}).get('enabled', True):
            log_path = Path(log_config.get('file', {}).get('path', './logs'))
            log_path.mkdir(parents=True, exist_ok=True)
            
            error_filename = log_config.get('error_file', {}).get('filename', 'futu_trading_errors_{time:YYYYMMDD}.log')
            error_log_file = log_path / error_filename
            
            _logger.add(
                str(error_log_file),
                format=log_config.get('format', DEFAULT_CONFIG['logging']['format']),
                level="ERROR",
                rotation=log_config.get('file', {}).get('rotation', '1 day'),
                retention=log_config.get('file', {}).get('retention', '30 days'),
                compression=log_config.get('file', {}).get('compression', 'zip'),
                enqueue=True,
                encoding='utf-8'
            )


def get_logger(name: Optional[str] = None):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        loguru.logger: Configured logger instance
    """
    # Ensure logger is configured
    LoggerConfig()
    
    if name:
        return _logger.bind(name=name)
    return _logger


# Convenience exports for compatibility
setup_logger = get_logger

# Export logger for direct import
logger = _logger


# Convenience function for quick logging
def info(message: str):
    """Log info message"""
    get_logger().info(message)


def debug(message: str):
    """Log debug message"""
    get_logger().debug(message)


def warning(message: str):
    """Log warning message"""
    get_logger().warning(message)


def error(message: str, exc_info: bool = False):
    """Log error message"""
    get_logger().error(message, exc_info=exc_info)


def critical(message: str, exc_info: bool = False):
    """Log critical message"""
    get_logger().critical(message, exc_info=exc_info)


# Initialize on module import
LoggerConfig()
