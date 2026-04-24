"""
Alfred Browser 測試腳本
測試所有 Browser 模式
"""

import sys
import os

# 添加技能路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alfred_browser import (
    AlfredBrowser, ChromeMCP, ChromeAttach, AgentBrowser, BrowserAuto,
    BrowserConfig, BrowserMode
)


def test_chrome_mcp():
    """測試 Chrome MCP 模式"""
    print("\n" + "="*60)
    print("🧪 測試 Chrome MCP 模式")
    print("="*60)
    
    try:
        mcp = ChromeMCP()
        
        # 測試連接
        print("\n1. 測試 CDP 連接...")
        result = mcp._check_connection()
        print(f"   結果: {'✅ 成功' if result else '❌ 失敗'}")
        
        if result:
            # 測試獲取頁面列表
            print("\n2. 測試獲取頁面列表...")
            pages = mcp.get_accessibility_tree()
            print(f"   結果: {pages.get('status', 'unknown')}")
            if 'pages' in pages:
                print(f"   頁面數: {len(pages['pages'])}")
        
        return result
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return False


def test_chrome_attach():
    """測試 Chrome Attach 模式"""
    print("\n" + "="*60)
    print("🧪 測試 Chrome Attach 模式")
    print("="*60)
    
    try:
        attach = ChromeAttach()
        
        # 測試列出分頁
        print("\n1. 測試列出分頁...")
        tabs = attach.list_tabs()
        print(f"   找到 {len(tabs)} 個分頁")
        
        return True
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return False


def test_agent_browser():
    """測試 Agent Browser 模式"""
    print("\n" + "="*60)
    print("🧪 測試 Agent Browser 模式")
    print("="*60)
    
    try:
        # 檢查是否安裝
        import subprocess
        result = subprocess.run(
            ["agent-browser", "--version"],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("   ⚠️ agent-browser 未安裝")
            return False
        
        print(f"   ✅ agent-browser 版本: {result.stdout.strip()}")
        
        ab = AgentBrowser()
        
        # 測試開啟頁面
        print("\n1. 測試開啟頁面...")
        output = ab.open("https://example.com")
        print(f"   輸出長度: {len(output)} 字符")
        
        # 測試截圖
        print("\n2. 測試獲取頁面結構...")
        snapshot = ab.snapshot(interactive=True)
        print(f"   結果: {snapshot.get('snapshot', 'N/A')[:100]}...")
        
        # 關閉
        print("\n3. 測試關閉...")
        ab.close()
        print("   ✅ 已關閉")
        
        return True
    except FileNotFoundError:
        print("   ⚠️ agent-browser 未安裝，請運行: npm install -g agent-browser")
        return False
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return False


def test_browser_auto():
    """測試 Browser Automation 模式"""
    print("\n" + "="*60)
    print("🧪 測試 Browser Automation 模式")
    print("="*60)
    
    try:
        # 檢查是否安裝
        import subprocess
        result = subprocess.run(
            ["browser", "--version"],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("   ⚠️ browser (Stagehand) 未安裝")
            return False
        
        print(f"   ✅ browser 版本: {result.stdout.strip()}")
        
        auto = BrowserAuto()
        
        # 測試導航
        print("\n1. 測試導航...")
        output = auto.navigate("https://example.com")
        print(f"   輸出長度: {len(output)} 字符")
        
        # 關閉
        print("\n2. 測試關閉...")
        auto.close()
        print("   ✅ 已關閉")
        
        return True
    except FileNotFoundError:
        print("   ⚠️ browser (Stagehand) 未安裝")
        print("   請前往 ~/.openclaw/skills/browser-automation 運行 npm install && npm link")
        return False
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return False


def test_alfred_browser():
    """測試 AlfredBrowser 智能路由"""
    print("\n" + "="*60)
    print("🧪 測試 AlfredBrowser 智能路由")
    print("="*60)
    
    try:
        print("\n1. 自動檢測模式...")
        browser = AlfredBrowser()
        mode = browser.get_mode()
        controller = browser.get_controller()
        
        print(f"   ✅ 檢測到的模式: {mode.value}")
        print(f"   ✅ 控制器類型: {type(controller).__name__}")
        
        return True
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return False


def test_forced_modes():
    """測試強制模式"""
    print("\n" + "="*60)
    print("🧪 測試強制模式")
    print("="*60)
    
    modes = [
        BrowserMode.CHROME_MCP,
        BrowserMode.CHROME_ATTACH,
        BrowserMode.AGENT_BROWSER,
        BrowserMode.BROWSER_AUTO
    ]
    
    for mode in modes:
        print(f"\n測試 {mode.value}...")
        try:
            browser = AlfredBrowser(force_mode=mode)
            print(f"   ✅ 成功初始化: {browser.get_mode().value}")
        except Exception as e:
            print(f"   ⚠️ 初始化失敗: {e}")


def main():
    """主測試函數"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🌐 Alfred Browser 測試套件 v1.0                    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = {
        "Chrome MCP": test_chrome_mcp(),
        "Chrome Attach": test_chrome_attach(),
        "Agent Browser": test_agent_browser(),
        "Browser Auto": test_browser_auto(),
        "Alfred Browser": test_alfred_browser(),
    }
    
    # 強制模式測試
    test_forced_modes()
    
    # 總結
    print("\n" + "="*60)
    print("📊 測試總結")
    print("="*60)
    
    for name, result in results.items():
        icon = "✅" if result else "❌"
        status = "通過" if result else "失敗"
        print(f"{icon} {name}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\n總計: {passed}/{total} 通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！")
    else:
        print("\n⚠️ 部分測試失敗，請檢查配置")


if __name__ == "__main__":
    main()
