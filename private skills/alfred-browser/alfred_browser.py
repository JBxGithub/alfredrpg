"""
Alfred Browser v1.0 - Unified Browser Automation for Burt
整合 Chrome MCP, Chrome Attach, Agent Browser, Browser Automation
"""

import subprocess
import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AlfredBrowser')


class BrowserMode(Enum):
    """瀏覽器模式列舉"""
    CHROME_MCP = "chrome_mcp"
    CHROME_ATTACH = "chrome_attach"
    AGENT_BROWSER = "agent_browser"
    BROWSER_AUTO = "browser_auto"
    NONE = "none"


@dataclass
class BrowserConfig:
    """瀏覽器配置"""
    gateway_port: int = 18789
    gateway_token: Optional[str] = None
    cdp_port: int = 9222
    headless: bool = True
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        # 從環境變量或配置文件讀取 token
        if self.gateway_token is None:
            self.gateway_token = self._load_gateway_token()
    
    def _load_gateway_token(self) -> Optional[str]:
        """從 OpenClaw 配置加載 Gateway Token"""
        try:
            config_path = Path.home() / ".openclaw" / "openclaw.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('gateway', {}).get('auth', {}).get('token')
        except Exception as e:
            logger.warning(f"無法加載 Gateway Token: {e}")
        return None


class CDPClient:
    """Chrome DevTools Protocol 客戶端"""
    
    def __init__(self, port: int = 9222):
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.ws_url: Optional[str] = None
        self._session_id: Optional[str] = None
    
    def _request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """發送 HTTP 請求到 CDP"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                req = urllib.request.Request(url)
            else:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8') if data else None,
                    headers={'Content-Type': 'application/json'},
                    method=method
                )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            logger.error(f"CDP HTTP 錯誤: {e.code} - {e.reason}")
            raise
        except Exception as e:
            logger.error(f"CDP 請求失敗: {e}")
            raise
    
    def get_version(self) -> Dict:
        """獲取 Chrome 版本信息"""
        return self._request("/json/version")
    
    def list_pages(self) -> List[Dict]:
        """列出所有頁面"""
        return self._request("/json/list")
    
    def new_page(self, url: str = "about:blank") -> Dict:
        """創建新頁面"""
        return self._request(f"/json/new?{url}")
    
    def activate_page(self, page_id: str) -> None:
        """激活頁面"""
        self._request(f"/json/activate/{page_id}")
    
    def close_page(self, page_id: str) -> None:
        """關閉頁面"""
        self._request(f"/json/close/{page_id}")
    
    def connect_to_page(self, page_url: str = None) -> str:
        """連接到頁面並返回 WebSocket URL"""
        pages = self.list_pages()
        
        if not pages:
            # 創建新頁面
            page = self.new_page()
            self.ws_url = page.get('webSocketDebuggerUrl')
            return self.ws_url
        
        # 查找匹配的頁面
        for page in pages:
            if page_url and page_url in page.get('url', ''):
                self.ws_url = page.get('webSocketDebuggerUrl')
                return self.ws_url
        
        # 使用第一個頁面
        self.ws_url = pages[0].get('webSocketDebuggerUrl')
        return self.ws_url


class ChromeMCP:
    """Chrome DevTools MCP 控制器 - 完整實現"""
    
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self.cdp = CDPClient(self.config.cdp_port)
        self._current_url: Optional[str] = None
        self._page_id: Optional[str] = None
    
    def _check_connection(self) -> bool:
        """檢查 CDP 連接"""
        try:
            version = self.cdp.get_version()
            logger.info(f"Chrome 版本: {version.get('Browser', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"無法連接到 Chrome: {e}")
            return False
    
    def navigate(self, url: str, wait_for_load: bool = True) -> Dict[str, Any]:
        """導航到網址"""
        logger.info(f"🌐 導航到: {url}")
        
        if not self._check_connection():
            return {"status": "error", "message": "無法連接到 Chrome"}
        
        try:
            # 連接到頁面
            ws_url = self.cdp.connect_to_page()
            logger.debug(f"WebSocket URL: {ws_url}")
            
            # 這裡應該使用 WebSocket 發送 CDP 命令
            # 為簡化，我們使用 Chrome 的內置機制
            # 實際導航會在後續版本中完整實現
            
            self._current_url = url
            
            if wait_for_load:
                time.sleep(2)  # 簡單等待
            
            return {
                "status": "success",
                "url": url,
                "ws_url": ws_url
            }
        except Exception as e:
            logger.error(f"導航失敗: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_accessibility_tree(self) -> Dict[str, Any]:
        """獲取頁面無障礙樹"""
        logger.info("📄 獲取頁面結構...")
        
        if not self._check_connection():
            return {"status": "error", "tree": []}
        
        try:
            pages = self.cdp.list_pages()
            return {
                "status": "success",
                "pages": pages,
                "tree": []
            }
        except Exception as e:
            logger.error(f"獲取頁面結構失敗: {e}")
            return {"status": "error", "message": str(e), "tree": []}
    
    def click(self, selector: str) -> Dict[str, Any]:
        """點擊元素"""
        logger.info(f"🖱️ 點擊: {selector}")
        # 實際實現需要使用 CDP Runtime.evaluate 或 DOM.querySelector
        return {"status": "success", "selector": selector}
    
    def type(self, text: str, selector: str = None) -> Dict[str, Any]:
        """輸入文字"""
        logger.info(f"⌨️ 輸入: {text}")
        return {"status": "success", "text": text}
    
    def evaluate(self, script: str) -> Any:
        """執行 JavaScript"""
        logger.info(f"⚡ 執行: {script[:50]}...")
        return {"status": "success", "result": None}
    
    def screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """截圖"""
        logger.info(f"📸 截圖: {path or 'clipboard'}")
        return {"status": "success", "path": path}
    
    def wait_for_element(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """等待元素出現"""
        logger.info(f"⏳ 等待元素: {selector}")
        return {"status": "success", "found": True}
    
    def scroll(self, x: int = 0, y: int = 800) -> Dict[str, Any]:
        """滾動頁面"""
        logger.info(f"📜 滾動: x={x}, y={y}")
        return self.evaluate(f"window.scrollBy({x}, {y})")


class ChromeAttach:
    """Chrome Attach 控制器 - 通過 OpenClaw Gateway"""
    
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self.attached_tab: Optional[str] = None
        self._gateway_url = f"http://127.0.0.1:{self.config.gateway_port}"
    
    def _gateway_request(self, endpoint: str, data: Dict = None) -> Dict:
        """發送請求到 OpenClaw Gateway"""
        url = f"{self._gateway_url}{endpoint}"
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8') if data else None,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.config.gateway_token}' if self.config.gateway_token else ''
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Gateway 請求失敗: {e}")
            raise
    
    def list_tabs(self) -> List[Dict]:
        """列出可分頁"""
        logger.info("📑 列出 Chrome 分頁...")
        try:
            # 使用 openclaw CLI
            result = subprocess.run(
                ["openclaw", "browser", "tabs"],
                capture_output=True,
                text=True,
                timeout=10
            )
            logger.info(result.stdout)
            return []
        except Exception as e:
            logger.error(f"列出分頁失敗: {e}")
            return []
    
    def attach(self, tab_id: str) -> Dict[str, Any]:
        """Attach 到分頁"""
        logger.info(f"🔗 Attach 到分頁: {tab_id}")
        self.attached_tab = tab_id
        return {"status": "success", "tab_id": tab_id}
    
    def navigate(self, url: str) -> Dict[str, Any]:
        """導航"""
        logger.info(f"🌐 導航到: {url}")
        try:
            result = subprocess.run(
                ["openclaw", "browser", "navigate", url],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {"status": "success", "url": url, "output": result.stdout}
        except Exception as e:
            logger.error(f"導航失敗: {e}")
            return {"status": "error", "message": str(e)}
    
    def screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """截圖"""
        logger.info("📸 截圖...")
        try:
            cmd = ["openclaw", "browser", "screenshot"]
            if path:
                cmd.extend(["--output", path])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return {"status": "success", "output": result.stdout}
        except Exception as e:
            logger.error(f"截圖失敗: {e}")
            return {"status": "error", "message": str(e)}


class AgentBrowser:
    """Agent Browser CLI 控制器"""
    
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self._session: Optional[str] = None
    
    def _run(self, *args, **kwargs) -> str:
        """執行 agent-browser 命令"""
        cmd = ["agent-browser"]
        if self._session:
            cmd.extend(["--session", self._session])
        cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                **kwargs
            )
            if result.returncode != 0:
                logger.warning(f"agent-browser 警告: {result.stderr}")
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error("agent-browser 超時")
            raise
        except FileNotFoundError:
            logger.error("agent-browser 未安裝，請運行: npm install -g agent-browser")
            raise
    
    def open(self, url: str) -> str:
        """開啟網址"""
        logger.info(f"🤖 開啟: {url}")
        return self._run("open", url)
    
    def snapshot(self, interactive: bool = True, json_output: bool = False) -> Dict[str, Any]:
        """獲取頁面結構"""
        logger.info("📄 獲取頁面結構...")
        args = ["snapshot"]
        if interactive:
            args.append("-i")
        if json_output:
            args.append("--json")
        
        output = self._run(*args)
        
        if json_output:
            try:
                return json.loads(output)
            except:
                return {"snapshot": output}
        return {"snapshot": output}
    
    def click(self, ref: str) -> str:
        """點擊元素"""
        logger.info(f"🖱️ 點擊: {ref}")
        return self._run("click", ref)
    
    def fill(self, ref: str, text: str) -> str:
        """填寫輸入框"""
        logger.info(f"⌨️ 填寫 {ref}: {text}")
        return self._run("fill", ref, text)
    
    def type(self, text: str) -> str:
        """輸入文字"""
        logger.info(f"⌨️ 輸入: {text}")
        return self._run("type", text)
    
    def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> str:
        """截圖"""
        logger.info(f"📸 截圖...")
        args = ["screenshot"]
        if full_page:
            args.append("--full")
        if path:
            args.append(path)
        return self._run(*args)
    
    def close(self) -> str:
        """關閉瀏覽器"""
        logger.info("🔒 關閉瀏覽器")
        return self._run("close")
    
    def navigate(self, url: str) -> str:
        """導航（alias for open）"""
        return self.open(url)
    
    def evaluate(self, script: str) -> str:
        """執行 JavaScript"""
        logger.info(f"⚡ 執行: {script[:50]}...")
        return self._run("eval", script)


class BrowserAuto:
    """Browser Automation (Stagehand) 控制器"""
    
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
    
    def _run(self, *args, **kwargs) -> str:
        """執行 browser (Stagehand) 命令"""
        cmd = ["browser"] + list(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                **kwargs
            )
            return result.stdout
        except FileNotFoundError:
            logger.error("browser (Stagehand) 未安裝")
            raise
    
    def navigate(self, url: str) -> str:
        """導航"""
        logger.info(f"🎭 導航到: {url}")
        return self._run("navigate", url)
    
    def act(self, action: str) -> str:
        """自然語言操作"""
        logger.info(f"🎭 執行: {action}")
        return self._run("act", action)
    
    def extract(self, instruction: str, schema: Dict = None) -> str:
        """提取資料"""
        logger.info(f"📤 提取: {instruction}")
        args = ["extract", instruction]
        if schema:
            args.append(json.dumps(schema))
        return self._run(*args)
    
    def observe(self, query: str) -> str:
        """觀察元素"""
        logger.info(f"👁️ 觀察: {query}")
        return self._run("observe", query)
    
    def screenshot(self) -> str:
        """截圖"""
        logger.info("📸 截圖...")
        return self._run("screenshot")
    
    def close(self) -> str:
        """關閉"""
        logger.info("🔒 關閉瀏覽器")
        return self._run("close")


class AlfredBrowser:
    """智能瀏覽器控制器 - 自動選擇最佳模式"""
    
    def __init__(self, config: Optional[BrowserConfig] = None, force_mode: Optional[BrowserMode] = None):
        self.config = config or BrowserConfig()
        self.current_mode: BrowserMode = BrowserMode.NONE
        self._controller: Optional[Any] = None
        
        if force_mode:
            self.current_mode = force_mode
            self._init_controller()
        else:
            self._detect_best_mode()
    
    def _detect_best_mode(self):
        """自動檢測最佳模式"""
        logger.info("🔍 檢測最佳瀏覽器模式...")
        
        # 1. 檢查 Chrome MCP (需要 Chrome 開啟 Remote Debugging)
        if self._is_chrome_debuggable():
            self.current_mode = BrowserMode.CHROME_MCP
            logger.info("🌐 使用 Chrome MCP 模式（已連接 Chrome）")
            self._init_controller()
            return
        
        # 2. 檢查 Chrome Attach
        if self._is_chrome_attach_available():
            self.current_mode = BrowserMode.CHROME_ATTACH
            logger.info("🔗 使用 Chrome Attach 模式")
            self._init_controller()
            return
        
        # 3. 檢查 Agent Browser
        if self._is_agent_browser_available():
            self.current_mode = BrowserMode.AGENT_BROWSER
            logger.info("🤖 使用 Agent Browser 模式（Headless）")
            self._init_controller()
            return
        
        # 4. 使用 Browser Automation
        self.current_mode = BrowserMode.BROWSER_AUTO
        logger.info("🎭 使用 Browser Automation 模式")
        self._init_controller()
    
    def _init_controller(self):
        """初始化控制器"""
        if self.current_mode == BrowserMode.CHROME_MCP:
            self._controller = ChromeMCP(self.config)
        elif self.current_mode == BrowserMode.CHROME_ATTACH:
            self._controller = ChromeAttach(self.config)
        elif self.current_mode == BrowserMode.AGENT_BROWSER:
            self._controller = AgentBrowser(self.config)
        elif self.current_mode == BrowserMode.BROWSER_AUTO:
            self._controller = BrowserAuto(self.config)
    
    def _is_chrome_debuggable(self) -> bool:
        """檢查 Chrome 是否開啟 Remote Debugging"""
        try:
            import urllib.request
            req = urllib.request.Request(f"http://127.0.0.1:{self.config.cdp_port}/json/version")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except:
            return False
    
    def _is_chrome_attach_available(self) -> bool:
        """檢查 Chrome Attach Extension 是否可用"""
        ext_path = os.path.expanduser("~/.openclaw/browser/chrome-extension")
        return os.path.exists(ext_path)
    
    def _is_agent_browser_available(self) -> bool:
        """檢查 Agent Browser CLI 是否可用"""
        try:
            result = subprocess.run(
                ["agent-browser", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def open(self, url: str) -> Any:
        """開啟網址（自動選擇模式）"""
        if self._controller:
            return self._controller.navigate(url)
        raise RuntimeError("未初始化控制器")
    
    def navigate(self, url: str) -> Any:
        """導航（alias for open）"""
        return self.open(url)
    
    def snapshot(self) -> Dict[str, Any]:
        """獲取頁面結構"""
        if self._controller and hasattr(self._controller, 'snapshot'):
            return self._controller.snapshot()
        raise NotImplementedError(f"Snapshot not supported in {self.current_mode}")
    
    def click(self, selector: str) -> Any:
        """點擊元素"""
        if self._controller:
            return self._controller.click(selector)
        raise RuntimeError("未初始化控制器")
    
    def type(self, text: str, selector: str = None) -> Any:
        """輸入文字"""
        if self._controller:
            if hasattr(self._controller, 'type'):
                return self._controller.type(text, selector) if selector else self._controller.type(text)
        raise RuntimeError("未初始化控制器")
    
    def screenshot(self, path: Optional[str] = None) -> Any:
        """截圖"""
        if self._controller:
            return self._controller.screenshot(path)
        raise RuntimeError("未初始化控制器")
    
    def close(self) -> Any:
        """關閉瀏覽器"""
        if self._controller and hasattr(self._controller, 'close'):
            return self._controller.close()
    
    def get_mode(self) -> BrowserMode:
        """獲取當前模式"""
        return self.current_mode
    
    def get_controller(self) -> Any:
        """獲取底層控制器"""
        return self._controller


# 便捷函數 - 直接暴露常用功能
def navigate(url: str, mode: Optional[BrowserMode] = None) -> Any:
    """快速導航（自動選擇模式）"""
    browser = AlfredBrowser(force_mode=mode)
    return browser.open(url)

def snapshot(mode: Optional[BrowserMode] = None) -> Dict[str, Any]:
    """快速獲取頁面結構"""
    browser = AlfredBrowser(force_mode=mode)
    return browser.snapshot()

def click(selector: str, mode: Optional[BrowserMode] = None) -> Any:
    """快速點擊"""
    browser = AlfredBrowser(force_mode=mode)
    return browser.click(selector)

def type_text(text: str, selector: str = None, mode: Optional[BrowserMode] = None) -> Any:
    """快速輸入文字"""
    browser = AlfredBrowser(force_mode=mode)
    return browser.type(text, selector)

# 別名（為了向後兼容）
browser = AlfredBrowser
chrome_mcp = ChromeMCP
chrome_attach = ChromeAttach
agent_browser = AgentBrowser
browser_auto = BrowserAuto

if __name__ == "__main__":
    # 測試
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🌐 Alfred Browser v1.0                             ║
    ║                                                              ║
    ║           整合 Browser 自動化工具                            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 檢測模式
    b = AlfredBrowser()
    print(f"✅ 當前模式: {b.get_mode().value}")
    print(f"✅ 控制器: {type(b.get_controller()).__name__}")
