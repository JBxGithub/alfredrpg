"""
Futu Trading Bot - 富途自動交易機器人
主程式入口
"""

import sys
import signal
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger
from src.config.settings import Settings
from src.core.bot import TradingBot


def signal_handler(signum, frame):
    """處理系統信號，優雅退出"""
    logger.info(f"收到信號 {signum}，正在關閉機器人...")
    if bot:
        bot.stop()
    sys.exit(0)


def main():
    """主函數"""
    global logger, bot
    
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 加載配置
        settings = Settings()
        
        # 設置日誌
        logger = setup_logger(settings)
        logger.info("=" * 50)
        logger.info("富途自動交易機器人啟動中...")
        logger.info("=" * 50)
        
        # 創建並啟動交易機器人
        bot = TradingBot(settings)
        bot.start()
        
    except Exception as e:
        if 'logger' in locals():
            logger.exception(f"機器人運行出錯: {e}")
        else:
            print(f"啟動失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
