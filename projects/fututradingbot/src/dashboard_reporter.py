"""
Dashboard Screenshot Scheduler - Dashboard定時截圖推送

每30分鐘截取Dashboard畫面並推送至WhatsApp
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

logger = get_logger(__name__)


class DashboardReporter:
    """Dashboard報告器"""
    
    def __init__(self, interval_minutes: int = 30):
        self.interval = interval_minutes
        self.dashboard_url = "http://127.0.0.1:8080"
        self.running = False
        
    async def start(self):
        """啟動報告循環"""
        logger.info("=" * 60)
        logger.info("Dashboard Reporter Started")
        logger.info(f"Interval: {self.interval} minutes")
        logger.info(f"Dashboard: {self.dashboard_url}")
        logger.info("=" * 60)
        
        self.running = True
        
        # Send initial report
        await self.send_report()
        
        # Start reporting loop
        while self.running:
            await asyncio.sleep(self.interval * 60)
            if self.running:
                await self.send_report()
    
    async def send_report(self):
        """發送報告"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Create report message
            message = f"""
📊 **FutuTradingBot 模擬交易報告** ({now})

🌐 Dashboard: http://127.0.0.1:8080
🔑 密碼: futu2024

請在電腦上查看詳細數據。

下次報告: {self.interval}分鐘後
            """.strip()
            
            # Log the report
            logger.info(f"Report scheduled: {now}")
            
            # Save to file for OpenClaw to pick up
            report_file = Path("reports/dashboard_report.txt")
            report_file.parent.mkdir(exist_ok=True)
            report_file.write_text(message, encoding='utf-8')
            
            logger.info(f"Report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Report error: {e}")
    
    def stop(self):
        """停止報告器"""
        self.running = False
        logger.info("Dashboard Reporter stopped")


async def main():
    """主函數"""
    reporter = DashboardReporter(interval_minutes=30)
    
    try:
        await reporter.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    finally:
        reporter.stop()


if __name__ == "__main__":
    asyncio.run(main())
