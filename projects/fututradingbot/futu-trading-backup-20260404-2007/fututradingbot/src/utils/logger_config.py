"""
日誌配置模組 - 統一日誌記錄
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """
    設置統一日誌記錄器
    
    Args:
        name: 日誌名稱
        log_file: 日誌檔案路徑（可選）
        level: 日誌級別
        
    Returns:
        logger 實例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重複添加 handler
    if logger.handlers:
        return logger
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台輸出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 檔案輸出（如指定）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class TradeLogger:
    """交易日誌記錄器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 按日期創建日誌檔案
        date_str = datetime.now().strftime("%Y%m%d")
        self.trade_log = self.log_dir / f"trades_{date_str}.csv"
        self.system_log = self.log_dir / f"system_{date_str}.log"
        
        # 初始化系統日誌
        self.logger = setup_logger("TradeLogger", str(self.system_log))
        
        # 初始化交易日誌檔案
        if not self.trade_log.exists():
            with open(self.trade_log, 'w', encoding='utf-8') as f:
                f.write("timestamp,symbol,action,direction,quantity,price,fee,pnl,reason\n")
    
    def log_trade(self, trade_data: dict):
        """記錄交易"""
        try:
            with open(self.trade_log, 'a', encoding='utf-8') as f:
                f.write(f"{trade_data.get('timestamp','')},{trade_data.get('symbol','')},"
                       f"{trade_data.get('action','')},{trade_data.get('direction','')},"
                       f"{trade_data.get('quantity',0)},{trade_data.get('price',0)},"
                       f"{trade_data.get('fee',0)},{trade_data.get('realized_pnl',0)},"
                       f"{trade_data.get('reason','')}\n")
            self.logger.info(f"Trade logged: {trade_data.get('action')} {trade_data.get('symbol')}")
        except Exception as e:
            self.logger.error(f"Failed to log trade: {e}")
    
    def log_system(self, message: str, level: str = "info"):
        """記錄系統訊息"""
        if level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)
