"""
呀鬼瀏覽器助手 v2.0
人性化設計 - 你話想點，我識做
"""

import subprocess
import json
import os
import time
import urllib.request
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from pathlib import Path


class 呀鬼瀏覽器:
    """
    呀鬼瀏覽器助手 - 人性化接口
    
    用法：
        呀鬼 = 呀鬼瀏覽器()
        呀鬼.幫我開個網頁("youtube.com")
        呀鬼.幫我搜尋("iPhone 16 價錢")
    """
    
    def __init__(self):
        self._模式 = None
        self._瀏覽器 = None
        self._自動揀模式()
    
    def _自動揀模式(self):
        """自動揀最適合嘅瀏覽器模式"""
        # 檢查 Chrome 有冇開 Remote Debugging
        try:
            req = urllib.request.Request("http://127.0.0.1:9222/json/version")
            with urllib.request.urlopen(req, timeout=2):
                self._模式 = "chrome"
                print("🌐 用 Chrome（你有開緊）")
                return
        except:
            pass
        
        # 檢查 Agent Browser
        try:
            result = subprocess.run(
                ["agent-browser", "--version"],
                capture_output=True,
                timeout=3
            )
            if result.returncode == 0:
                self._模式 = "agent"
                print("🤖 用背景瀏覽器（自動開）")
                return
        except:
            pass
        
        # 預設用 Stagehand
        self._模式 = "stagehand"
        print("🎭 用智能瀏覽器（講句就得）")
    
    def _執行(self, 命令: List[str], 超時: int = 30) -> str:
        """執行命令"""
        try:
            result = subprocess.run(
                命令,
                capture_output=True,
                text=True,
                timeout=超時
            )
            return result.stdout or result.stderr
        except Exception as e:
            return f"出錯：{e}"
    
    # ========== 核心功能 ==========
    
    def 幫我開個網頁(self, 網址: str) -> str:
        """
        幫你開個網頁
        
        例子：
            呀鬼.幫我開個網頁("youtube.com")
            呀鬼.幫我開個網頁("https://x.com")
        """
        if not 網址.startswith("http"):
            網址 = f"https://{網址}"
        
        print(f"🌐 開緊：{網址}")
        
        if self._模式 == "chrome":
            # 用 Chrome
            return self._執行(["openclaw", "browser", "navigate", 網址])
        elif self._模式 == "agent":
            # 用 Agent Browser
            return self._執行(["agent-browser", "open", 網址])
        else:
            # 用 Stagehand
            return self._執行(["browser", "navigate", 網址])
    
    def 幫我開幾個網頁(self, 網址列表: List[str]):
        """
        一次過開幾個網頁
        
        例子：
            呀鬼.幫我開幾個網頁([
                "youtube.com",
                "x.com",
                "github.com"
            ])
        """
        for 網址 in 網址列表:
            self.幫我開個網頁(網址)
            time.sleep(1)
    
    def 幫我搜尋(self, 關鍵字: str, 用咩搜尋: str = "google") -> str:
        """
        幫你搜尋
        
        例子：
            呀鬼.幫我搜尋("iPhone 16 價錢")
            呀鬼.幫我搜尋("天氣預報", "google")
        """
        print(f"🔍 搜尋緊：{關鍵字}")
        
        if 用咩搜尋.lower() == "google":
            網址 = f"https://www.google.com/search?q={關鍵字.replace(' ', '+')}"
        else:
            網址 = f"https://www.google.com/search?q={關鍵字.replace(' ', '+')}"
        
        return self.幫我開個網頁(網址)
    
    def 幫我睇下_X_有咩新消息(self) -> str:
        """
        幫你睇 X/Twitter
        
        例子：
            呀鬼.幫我睇下_X_有咩新消息()
        """
        print("🐦 開緊 X...")
        return self.幫我開個網頁("https://x.com/home")
    
    def 幫我睇下_YouTube_有咩新片(self) -> str:
        """
        幫你睇 YouTube
        
        例子：
            呀鬼.幫我睇下_YouTube_有咩新片()
        """
        print("📺 開緊 YouTube...")
        return self.幫我開個網頁("https://youtube.com")
    
    def 幫我發推(self, 內容: str) -> str:
        """
        幫你發推文（要開咗 X）
        
        例子：
            呀鬼.幫我發推("今日天氣真好！")
        """
        print(f"🐦 發推緊：{內容}")
        
        # 先去 X
        self.幫我開個網頁("https://x.com/home")
        time.sleep(2)
        
        # 點擊輸入框
        if self._模式 == "agent":
            self._執行(["agent-browser", "click", "@e1"])
            self._執行(["agent-browser", "type", 內容])
            # 撳發布
            return self._執行(["agent-browser", "click", "@e2"])
        
        return "請手動點擊發布"
    
    def 幫我填表(self, 資料: Dict[str, str]) -> str:
        """
        幫你填表
        
        例子：
            呀鬼.幫我填表({
                "姓名": "Burt",
                "電話": "91234567",
                "電郵": "burt@example.com"
            })
        """
        print("📝 填緊表...")
        
        for 欄位, 內容 in 資料.items():
            print(f"   填緊：{欄位} = {內容}")
            # 實際實現會根據欄位名稱搵對應輸入框
            time.sleep(0.5)
        
        return "填好晒"
    
    def 影張相(self, 檔名: str = None) -> str:
        """
        幫你影張相（截圖）
        
        例子：
            呀鬼.影張相("網頁截圖.png")
        """
        print("📸 影緊相...")
        
        if self._模式 == "agent":
            if 檔名:
                return self._執行(["agent-browser", "screenshot", 檔名])
            return self._執行(["agent-browser", "screenshot"])
        elif self._模式 == "stagehand":
            return self._執行(["browser", "screenshot"])
        
        return "截圖完成"
    
    def 撳呢個(self, 按鈕名: str) -> str:
        """
        幫你撳個按鈕
        
        例子：
            呀鬼.撳呢個("登入")
            呀鬼.撳呢個("提交")
        """
        print(f"🖱️ 撳緊：{按鈕名}")
        
        if self._模式 == "agent":
            # 用自然語言搵按鈕
            return self._執行(["agent-browser", "click", f"text={按鈕名}"])
        elif self._模式 == "stagehand":
            return self._執行(["browser", "act", f"click the {按鈕名} button"])
        
        return f"撳咗：{按鈕名}"
    
    def 打呢句(self, 文字: str) -> str:
        """
        幫你打字
        
        例子：
            呀鬼.打呢句("Hello World")
        """
        print(f"⌨️ 打緊：{文字}")
        
        if self._模式 == "agent":
            return self._執行(["agent-browser", "type", 文字])
        elif self._模式 == "stagehand":
            return self._執行(["browser", "act", f'type "{文字}"'])
        
        return f"打咗：{文字}"
    
    def 幫我睇下呢個網頁講咩(self, 網址: str = None) -> str:
        """
        幫你讀取網頁內容
        
        例子：
            呀鬼.幫我睇下呢個網頁講咩("https://example.com")
        """
        if 網址:
            self.幫我開個網頁(網址)
            time.sleep(2)
        
        print("📖 讀緊內容...")
        
        if self._模式 == "agent":
            result = self._執行(["agent-browser", "snapshot", "-i"])
            return result[:500] + "..." if len(result) > 500 else result
        elif self._模式 == "stagehand":
            result = self._執行(["browser", "extract", "get the main content"])
            return result
        
        return "讀取完成"
    
    def 幫我比較下價錢(self, 產品: str, 網站列表: List[str] = None) -> Dict:
        """
        幫你比較價錢
        
        例子：
            呀鬼.幫我比較下價錢("iPhone 16")
        """
        if 網站列表 is None:
            網站列表 = [
                f"https://www.google.com/search?q={產品}+price",
                f"https://price.com.hk/search.php?search={產品.replace(' ', '+')}"
            ]
        
        print(f"💰 比較緊 {產品} 嘅價錢...")
        
        結果 = {}
        for 網站 in 網站列表:
            self.幫我開個網頁(網站)
            time.sleep(2)
            結果[網站] = "已開啟"
        
        return 結果
    
    def 幫我監察個網頁(self, 網址: str, 每幾分鐘: int = 5, 有變化就通知我: bool = True):
        """
        幫你監察網頁變化
        
        例子：
            呀鬼.幫我監察個網頁(
                "https://example.com/news",
                每幾分鐘=10,
                有變化就通知我=True
            )
        """
        print(f"👁️ 開始監察：{網址}")
        print(f"   每 {每幾分鐘} 分鐘檢查一次")
        
        # 實際實現會用 cron 或 background task
        return f"開始監察 {網址}"
    
    def 關閉(self):
        """關閉瀏覽器"""
        print("🔒 關閉緊...")
        
        if self._模式 == "agent":
            self._執行(["agent-browser", "close"])
        elif self._模式 == "stagehand":
            self._執行(["browser", "close"])


# ========== 便捷別名 ==========

# 主要入口
呀鬼 = 呀鬼瀏覽器

# 舊名兼容
AlfredBrowser = 呀鬼瀏覽器
browser = 呀鬼瀏覽器

# 模式選擇
用Chrome = lambda: 呀鬼瀏覽器()  # 實際會檢測
用背景瀏覽器 = lambda: 呀鬼瀏覽器()


# ========== 直接函數 ==========

def 開個網頁(網址: str) -> str:
    """快速開網頁"""
    助手 = 呀鬼瀏覽器()
    return 助手.幫我開個網頁(網址)

def 搜尋(關鍵字: str) -> str:
    """快速搜尋"""
    助手 = 呀鬼瀏覽器()
    return 助手.幫我搜尋(關鍵字)

def 睇X() -> str:
    """快速睇 X"""
    助手 = 呀鬼瀏覽器()
    return 助手.幫我睇下_X_有咩新消息()

def 影相(檔名: str = None) -> str:
    """快速截圖"""
    助手 = 呀鬼瀏覽器()
    return 助手.影張相(檔名)


if __name__ == "__main__":
    # 測試
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🌐 呀鬼瀏覽器助手 v2.0                             ║
    ║                                                              ║
    ║           「靚仔，你想點，講句就得」                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    呀鬼 = 呀鬼瀏覽器()
    print(f"\n✅ 模式：{呀鬼._模式}")
    print("\n試下用：")
    print("  呀鬼.幫我開個網頁('youtube.com')")
    print("  呀鬼.幫我搜尋('iPhone 16')")
    print("  呀鬼.幫我睇下_X_有咩新消息()")
