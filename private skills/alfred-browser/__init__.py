"""
呀鬼瀏覽器助手 v2.0
人性化設計 - 你話想點，我識做

用法：
    from skills.alfred_browser import 呀鬼
    
    # 講句就得
    呀鬼.幫我開個網頁("youtube.com")
    呀鬼.幫我搜尋("iPhone 16 價錢")
    呀鬼.幫我睇下_X_有咩新消息()
"""

from .呀鬼 import (
    呀鬼瀏覽器,
    呀鬼,
    開個網頁,
    搜尋,
    睇X,
    影相,
    用Chrome,
    用背景瀏覽器,
    # 舊名兼容
    AlfredBrowser,
    browser,
)

__version__ = "2.0.0"
__author__ = "Alfred"

__all__ = [
    # 主要入口
    "呀鬼瀏覽器",
    "呀鬼",
    # 便捷函數
    "開個網頁",
    "搜尋",
    "睇X",
    "影相",
    # 模式選擇
    "用Chrome",
    "用背景瀏覽器",
    # 舊名兼容
    "AlfredBrowser",
    "browser",
]
