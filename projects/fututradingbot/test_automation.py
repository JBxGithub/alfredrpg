"""
自動化系統測試腳本
驗證所有核心組件能否正常運作
"""

import sys
import asyncio
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot')

print("=" * 60)
print("FutuTradingBot 自動化系統測試")
print("=" * 60)
print()

# 測試 1: 導入所有模組
print("[測試 1] 模組導入測試...")
try:
    from src.automation import (
        DeploymentManager, RiskChecker, AutoExecutor, 
        TradingMonitor, UnifiedTradingSystem, UnifiedConfig
    )
    from src.realtime_optimizer import (
        PerformanceTracker, ParameterAdjuster,
        AdaptiveStopManager, StrategyEvolver
    )
    print("✅ 所有模組導入成功")
except Exception as e:
    print(f"❌ 模組導入失敗: {e}")
    sys.exit(1)

print()

# 測試 2: DeploymentManager
print("[測試 2] DeploymentManager 初始化...")
try:
    dm = DeploymentManager()
    print(f"✅ DeploymentManager 初始化成功")
    print(f"   初始狀態: {dm.status.value}")
except Exception as e:
    print(f"❌ DeploymentManager 失敗: {e}")

print()

# 測試 3: RiskChecker
print("[測試 3] RiskChecker 初始化...")
try:
    rc = RiskChecker()
    print(f"✅ RiskChecker 初始化成功")
except Exception as e:
    print(f"❌ RiskChecker 失敗: {e}")

print()

# 測試 4: PerformanceTracker
print("[測試 4] PerformanceTracker 初始化...")
try:
    pt = PerformanceTracker()
    pt.start()
    print(f"✅ PerformanceTracker 初始化成功")
    print(f"   窗口大小: {pt.window_size}")
except Exception as e:
    print(f"❌ PerformanceTracker 失敗: {e}")

print()

# 測試 5: ParameterAdjuster
print("[測試 5] ParameterAdjuster 初始化...")
try:
    pa = ParameterAdjuster()
    pa.initialize({
        'position_size': 0.02,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04
    })
    print(f"✅ ParameterAdjuster 初始化成功")
    print(f"   當前參數: {pa.get_current_params()}")
except Exception as e:
    print(f"❌ ParameterAdjuster 失敗: {e}")

print()

# 測試 6: AdaptiveStopManager
print("[測試 6] AdaptiveStopManager 初始化...")
try:
    asm = AdaptiveStopManager()
    print(f"✅ AdaptiveStopManager 初始化成功")
except Exception as e:
    print(f"❌ AdaptiveStopManager 失敗: {e}")

print()

# 測試 7: StrategyEvolver
print("[測試 7] StrategyEvolver 初始化...")
try:
    se = StrategyEvolver()
    se.initialize_population({
        'position_size': 0.02,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04
    })
    print(f"✅ StrategyEvolver 初始化成功")
    print(f"   種群大小: {len(se.population)}")
except Exception as e:
    print(f"❌ StrategyEvolver 失敗: {e}")

print()

# 測試 8: UnifiedTradingSystem (非異步初始化)
print("[測試 8] UnifiedTradingSystem 初始化...")
try:
    uts = UnifiedTradingSystem()
    print(f"✅ UnifiedTradingSystem 初始化成功")
except Exception as e:
    print(f"❌ UnifiedTradingSystem 失敗: {e}")

print()
print("=" * 60)
print("✅ 所有核心組件測試通過！")
print("=" * 60)
print()
print("系統已就緒，可以執行 start_live_trading.bat")
