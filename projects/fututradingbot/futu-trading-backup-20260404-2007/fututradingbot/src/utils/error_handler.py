"""
錯誤處理模組 - 統一錯誤處理和重試機制
"""

import functools
import time
import logging
from typing import Callable, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TradingError(Exception):
    """交易相關錯誤"""
    pass


class ConnectionError(TradingError):
    """連接錯誤"""
    pass


class OrderError(TradingError):
    """訂單錯誤"""
    pass


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    重試裝飾器
    
    Args:
        max_retries: 最大重試次數
        delay: 初始延遲（秒）
        backoff: 退避系數
        exceptions: 需要重試的錯誤類型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    default_return: Any = None,
    error_message: str = None,
    log_error: bool = True
) -> Any:
    """
    安全執行函數，捕獲所有錯誤
    
    Args:
        func: 要執行的函數
        default_return: 錯誤時的默認返回值
        error_message: 自定義錯誤訊息
        log_error: 是否記錄錯誤
        
    Returns:
        函數返回值或默認值
    """
    try:
        return func()
    except Exception as e:
        if log_error:
            msg = error_message or f"Error executing {func.__name__}: {e}"
            logger.error(msg)
        return default_return


class ErrorTracker:
    """錯誤追蹤器"""
    
    def __init__(self, max_errors: int = 100):
        self.errors = []
        self.max_errors = max_errors
    
    def add_error(self, error: Exception, context: str = None):
        """添加錯誤記錄"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'context': context
        }
        
        self.errors.append(error_info)
        
        # 限制錯誤記錄數量
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        logger.error(f"Error tracked: {error_info['type']} - {error_info['message']}")
    
    def get_recent_errors(self, count: int = 10) -> list:
        """獲取最近的錯誤"""
        return self.errors[-count:]
    
    def get_error_summary(self) -> dict:
        """獲取錯誤摘要"""
        if not self.errors:
            return {'total': 0, 'by_type': {}}
        
        by_type = {}
        for error in self.errors:
            error_type = error['type']
            by_type[error_type] = by_type.get(error_type, 0) + 1
        
        return {
            'total': len(self.errors),
            'by_type': by_type,
            'recent': self.get_recent_errors(5)
        }
    
    def clear(self):
        """清空錯誤記錄"""
        self.errors.clear()
