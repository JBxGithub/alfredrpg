"""
Alfred Browser Setup Script
自動配置所有 browser 相關工具
"""

import subprocess
import os
import sys
import json
from pathlib import Path

def print_step(step: str):
    print(f"\n{'='*50}")
    print(f"📋 {step}")
    print('='*50)

def check_node():
    """檢查 Node.js"""
    print_step("檢查 Node.js")
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"✅ Node.js: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Node.js 未安裝")
        return False

def check_agent_browser():
    """檢查 Agent Browser"""
    print_step("檢查 Agent Browser")
    try:
        result = subprocess.run(["agent-browser", "--version"], capture_output=True, text=True)
        print(f"✅ Agent Browser: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Agent Browser 未安裝")
        return False

def install_agent_browser():
    """安裝 Agent Browser"""
    print_step("安裝 Agent Browser")
    try:
        subprocess.run(["npm", "install", "-g", "agent-browser"], check=True)
        subprocess.run(["agent-browser", "install"], check=True)
        print("✅ Agent Browser 安裝完成")
        return True
    except Exception as e:
        print(f"❌ 安裝失敗: {e}")
        return False

def check_browser_auto():
    """檢查 Browser Automation"""
    print_step("檢查 Browser Automation (Stagehand)")
    skill_path = Path.home() / ".openclaw" / "skills" / "browser-automation"
    if skill_path.exists():
        print(f"✅ Browser Automation 技能存在: {skill_path}")
        # 檢查是否已安裝依賴
        if (skill_path / "node_modules").exists():
            print("✅ 依賴已安裝")
            return True
        else:
            print("⚠️ 需要安裝依賴")
            return False
    else:
        print("❌ Browser Automation 技能不存在")
        return False

def install_browser_auto():
    """安裝 Browser Automation 依賴"""
    print_step("安裝 Browser Automation 依賴")
    skill_path = Path.home() / ".openclaw" / "skills" / "browser-automation"
    try:
        os.chdir(skill_path)
        subprocess.run(["npm", "install"], check=True)
        subprocess.run(["npm", "link"], check=True)
        print("✅ Browser Automation 配置完成")
        return True
    except Exception as e:
        print(f"❌ 配置失敗: {e}")
        return False

def check_chrome_extension():
    """檢查 Chrome Extension"""
    print_step("檢查 Chrome Extension")
    ext_path = Path.home() / ".openclaw" / "browser" / "chrome-extension"
    if ext_path.exists():
        print(f"✅ Chrome Extension 存在: {ext_path}")
        return True
    else:
        print(f"❌ Chrome Extension 不存在")
        print(f"   預期路徑: {ext_path}")
        return False

def check_chrome_debugging():
    """檢查 Chrome Remote Debugging"""
    print_step("檢查 Chrome Remote Debugging")
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:9222/json/version")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                data = json.loads(response.read())
                print(f"✅ Chrome Remote Debugging 已啟用")
                print(f"   Chrome 版本: {data.get('Browser', 'Unknown')}")
                return True
    except Exception as e:
        print(f"❌ Chrome Remote Debugging 未啟用")
        print(f"   請前往 chrome://inspect/#remote-debugging 啟用")
        return False

def create_desktop_shortcut():
    """創建桌面快捷方式"""
    print_step("創建桌面快捷方式")
    ext_path = Path.home() / ".openclaw" / "browser" / "chrome-extension"
    desktop = Path.home() / "Desktop" / "OpenClaw-Extension"
    
    if ext_path.exists():
        try:
            import shutil
            if desktop.exists():
                shutil.rmtree(desktop)
            shutil.copytree(ext_path, desktop)
            print(f"✅ 已複製到桌面: {desktop}")
            print("   請在 Chrome 載入此擴展")
            return True
        except Exception as e:
            print(f"❌ 複製失敗: {e}")
            return False
    else:
        print("❌ Chrome Extension 不存在，無法創建快捷方式")
        return False

def get_gateway_token():
    """獲取 Gateway Token"""
    print_step("獲取 Gateway Token")
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            token = config.get('gateway', {}).get('auth', {}).get('token')
            if token:
                print(f"✅ Gateway Token: {token[:20]}...")
                return token
    except Exception as e:
        print(f"❌ 無法讀取配置: {e}")
    return None

def main():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🌐 Alfred Browser Setup v1.0                       ║
    ║                                                              ║
    ║           自動配置所有 Browser 工具                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = {
        "node": False,
        "agent_browser": False,
        "browser_auto": False,
        "chrome_ext": False,
        "chrome_debug": False
    }
    
    # 檢查 Node.js
    results["node"] = check_node()
    if not results["node"]:
        print("\n❌ 請先安裝 Node.js: https://nodejs.org/")
        return
    
    # 檢查 Agent Browser
    results["agent_browser"] = check_agent_browser()
    if not results["agent_browser"]:
        install = input("\n是否安裝 Agent Browser? (y/n): ")
        if install.lower() == 'y':
            results["agent_browser"] = install_agent_browser()
    
    # 檢查 Browser Automation
    results["browser_auto"] = check_browser_auto()
    if not results["browser_auto"]:
        install = input("\n是否安裝 Browser Automation 依賴? (y/n): ")
        if install.lower() == 'y':
            results["browser_auto"] = install_browser_auto()
    
    # 檢查 Chrome Extension
    results["chrome_ext"] = check_chrome_extension()
    if not results["chrome_ext"]:
        print("\n⚠️ Chrome Extension 缺失")
        print("   這是正常情況，Extension 需要手動安裝或從其他來源獲取")
    else:
        create = input("\n是否創建桌面快捷方式? (y/n): ")
        if create.lower() == 'y':
            create_desktop_shortcut()
    
    # 檢查 Chrome Debugging
    results["chrome_debug"] = check_chrome_debugging()
    
    # 顯示 Gateway Token
    token = get_gateway_token()
    
    # 總結
    print("\n" + "="*50)
    print("📊 配置總結")
    print("="*50)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {'完成' if status else '未完成'}")
    
    print("\n" + "="*50)
    print("📝 下一步")
    print("="*50)
    
    if not results["chrome_debug"]:
        print("1. 開啟 Chrome")
        print("2. 前往 chrome://inspect/#remote-debugging")
        print("3. 啟用 'Discover network targets'")
    
    if results["chrome_ext"]:
        print("\n4. 在 Chrome 載入 Extension:")
        print("   - 開啟 chrome://extensions")
        print("   - 啟用 Developer mode")
        print("   - 點擊 Load unpacked")
        print("   - 選擇 ~/Desktop/OpenClaw-Extension")
        print(f"   - 配置 Port: 18789")
        if token:
            print(f"   - 配置 Token: {token[:20]}...")
    
    print("\n✨ 配置完成！可以開始使用 Alfred Browser 了")

if __name__ == "__main__":
    main()
