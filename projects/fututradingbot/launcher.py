"""
FutuTradingBot 統一啟動器
管理所有組件的啟動和監控
"""

import asyncio
import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from datetime import datetime
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger("Launcher")

class Component:
    """系統組件"""
    def __init__(self, name: str, command: list, port: int, delay: int = 0):
        self.name = name
        self.command = command
        self.port = port
        self.delay = delay
        self.process = None
        self.status = "stopped"
    
    async def start(self):
        """啟動組件"""
        if self.delay > 0:
            logger.info(f"[{self.name}] 等待 {self.delay} 秒...")
            await asyncio.sleep(self.delay)
        
        logger.info(f"[{self.name}] 啟動中... (Port {self.port})")
        
        try:
            # 使用 CREATE_NEW_PROCESS_GROUP 以便正確終止
            if sys.platform == 'win32':
                self.process = subprocess.Popen(
                    self.command,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                self.process = subprocess.Popen(
                    self.command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid
                )
            
            # 等待服務就緒
            for i in range(30):  # 最多等待 30 秒
                await asyncio.sleep(1)
                if await self._check_port():
                    self.status = "running"
                    logger.info(f"[{self.name}] ✅ 啟動成功 (PID: {self.process.pid})")
                    return True
                if self.process.poll() is not None:
                    logger.error(f"[{self.name}] ❌ 進程已退出")
                    return False
            
            logger.warning(f"[{self.name}] ⚠️ 啟動超時，但進程仍在運行")
            self.status = "running"
            return True
            
        except Exception as e:
            logger.error(f"[{self.name}] ❌ 啟動失敗: {e}")
            self.status = "error"
            return False
    
    async def _check_port(self) -> bool:
        """檢查端口是否監聽"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection('127.0.0.1', self.port),
                timeout=1.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    def stop(self):
        """停止組件"""
        if self.process and self.process.poll() is None:
            logger.info(f"[{self.name}] 停止中...")
            try:
                if sys.platform == 'win32':
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                
                self.process.wait(timeout=5)
                self.status = "stopped"
                logger.info(f"[{self.name}] ✅ 已停止")
            except:
                self.process.kill()
                self.status = "stopped"
                logger.info(f"[{self.name}] ✅ 已強制停止")


class TradingSystemLauncher:
    """交易系統啟動器"""
    
    def __init__(self):
        self.workspace = Path(__file__).parent
        self.components = []
        self.running = False
        
        # 定義組件
        self.components.append(Component(
            name="實盤 Bridge",
            command=[sys.executable, str(self.workspace / "src" / "realtime_bridge.py")],
            port=8765,
            delay=0
        ))
        
        self.components.append(Component(
            name="實盤 Dashboard",
            command=[sys.executable, str(self.workspace / "src" / "dashboard" / "app.py")],
            port=8080,
            delay=5  # 等待 Bridge 啟動
        ))
        
        self.components.append(Component(
            name="模擬 Bridge",
            command=[sys.executable, str(self.workspace / "simulation" / "paper_trading_bridge.py")],
            port=8766,
            delay=2
        ))
        
        self.components.append(Component(
            name="模擬 Dashboard",
            command=[sys.executable, str(self.workspace / "simulation" / "paper_dashboard.py")],
            port=8081,
            delay=5
        ))
    
    async def start_all(self):
        """啟動所有組件"""
        logger.info("=" * 60)
        logger.info("FutuTradingBot 系統啟動器")
        logger.info("=" * 60)
        logger.info("")
        
        self.running = True
        
        # 清理現有進程
        logger.info("[系統] 清理現有進程...")
        await self._cleanup()
        
        # 依序啟動
        for component in self.components:
            success = await component.start()
            if not success:
                logger.error(f"[系統] {component.name} 啟動失敗，停止所有組件")
                await self.stop_all()
                return False
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ 所有系統啟動完成！")
        logger.info("=" * 60)
        logger.info("")
        logger.info("訪問地址:")
        logger.info("  實盤 Dashboard: http://127.0.0.1:8080")
        logger.info("  模擬 Dashboard: http://127.0.0.1:8081")
        logger.info("")
        logger.info("按 Ctrl+C 停止所有系統")
        logger.info("")
        
        # 保持運行
        try:
            while self.running:
                await self._monitor()
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass
        
        return True
    
    async def _monitor(self):
        """監控組件狀態"""
        for component in self.components:
            if component.status == "running":
                is_alive = await component._check_port()
                if not is_alive:
                    logger.warning(f"[{component.name}] ⚠️ 無響應，嘗試重啟...")
                    component.stop()
                    await component.start()
    
    async def stop_all(self):
        """停止所有組件"""
        logger.info("")
        logger.info("[系統] 停止所有組件...")
        
        self.running = False
        
        # 反向停止（先停 Dashboard，再停 Bridge）
        for component in reversed(self.components):
            component.stop()
        
        logger.info("[系統] ✅ 所有組件已停止")
    
    async def _cleanup(self):
        """清理現有進程"""
        try:
            # 查找並終止現有 Python 進程
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe"],
                capture_output=True,
                text=True
            )
            await asyncio.sleep(2)
        except:
            pass


async def main():
    """主函數"""
    launcher = TradingSystemLauncher()
    
    # 處理 Ctrl+C
    def signal_handler():
        asyncio.create_task(launcher.stop_all())
    
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    
    try:
        await launcher.start_all()
    except KeyboardInterrupt:
        await launcher.stop_all()


if __name__ == "__main__":
    asyncio.run(main())
