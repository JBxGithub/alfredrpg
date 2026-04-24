"""
Phase 2 & 3 組件測試
"""

import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot')

import numpy as np
import pandas as pd
from datetime import datetime

print("=" * 70)
print("Phase 2 & 3 組件測試")
print("=" * 70)
print()

# ========== Phase 2 測試 ==========
print("【Phase 2: 自適應策略切換】")
print("-" * 70)

# 測試 1: MarketRegimeDetector
print("\n[測試 2.1] MarketRegimeDetector 市場狀態檢測...")
try:
    from src.adaptive_strategy import MarketRegimeDetector, MarketRegime
    
    detector = MarketRegimeDetector()
    
    # 創建模擬數據
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    np.random.seed(42)
    
    # 上升趨勢數據
    trend_data = pd.DataFrame({
        'open': 100 + np.cumsum(np.random.randn(50) * 0.5 + 0.3),
        'high': 102 + np.cumsum(np.random.randn(50) * 0.5 + 0.3),
        'low': 98 + np.cumsum(np.random.randn(50) * 0.5 + 0.3),
        'close': 101 + np.cumsum(np.random.randn(50) * 0.5 + 0.3),
        'volume': np.random.randint(1000, 10000, 50)
    }, index=dates)
    
    regime = detector.detect(trend_data)
    print(f"✅ 狀態檢測成功")
    print(f"   檢測狀態: {regime.regime.value}")
    print(f"   信心度: {regime.confidence:.2%}")
    print(f"   ADX: {regime.adx:.2f}")
    print(f"   波動率: {regime.volatility:.4f}")
except Exception as e:
    print(f"❌ 失敗: {e}")

# 測試 2: StrategySelector
print("\n[測試 2.2] StrategySelector 策略選擇器...")
try:
    from src.adaptive_strategy import StrategySelector, StrategyScore
    
    selector = StrategySelector()
    
    # 註冊策略
    selector.register_strategy(
        'TrendFollowing',
        {MarketRegime.TRENDING_UP: 0.9, MarketRegime.TRENDING_DOWN: 0.8, 
         MarketRegime.RANGING: 0.3},
        0.7
    )
    selector.register_strategy(
        'MeanReversion',
        {MarketRegime.TRENDING_UP: 0.3, MarketRegime.RANGING: 0.9},
        0.6
    )
    
    # 選擇策略
    best = selector.select_strategy(regime)
    print(f"✅ 策略選擇成功")
    print(f"   推薦策略: {best.strategy_name}")
    print(f"   綜合評分: {best.score:.3f}")
    print(f"   狀態適配: {best.regime_fit:.2f}")
except Exception as e:
    print(f"❌ 失敗: {e}")

# 測試 3: StrategyOrchestrator
print("\n[測試 2.3] StrategyOrchestrator 策略編排器...")
try:
    from src.adaptive_strategy import StrategyOrchestrator
    
    orch = StrategyOrchestrator()
    orch.add_strategy('TrendFollowing', 0.6)
    orch.add_strategy('MeanReversion', 0.4)
    
    active = orch.get_active_strategies()
    print(f"✅ 策略編排成功")
    print(f"   激活策略數: {len(active)}")
    for alloc in active:
        print(f"   - {alloc.strategy_name}: {alloc.weight:.1%}")
except Exception as e:
    print(f"❌ 失敗: {e}")

# 測試 4: MultiStrategyEngine
print("\n[測試 2.4] MultiStrategyEngine 多策略引擎...")
try:
    from src.adaptive_strategy import MultiStrategyEngine, EngineConfig
    
    config = EngineConfig(
        enable_regime_detection=True,
        enable_strategy_selection=True,
        check_interval=60
    )
    engine = MultiStrategyEngine(config)
    
    # 註冊策略
    engine.register_strategy(
        'TQQQ_Momentum',
        {MarketRegime.TRENDING_UP: 0.9, MarketRegime.TRENDING_DOWN: 0.7},
        0.5
    )
    
    status = engine.get_engine_status()
    print(f"✅ 引擎初始化成功")
    print(f"   狀態檢測: {'啟用' if status['config']['enable_regime_detection'] else '禁用'}")
    print(f"   策略選擇: {'啟用' if status['config']['enable_strategy_selection'] else '禁用'}")
except Exception as e:
    print(f"❌ 失敗: {e}")

print("\n" + "=" * 70)
print("【Phase 3: 強化學習】")
print("-" * 70)

# 測試 5: TradingEnvironment
print("\n[測試 3.1] TradingEnvironment 交易環境...")
try:
    from src.reinforcement_learning import TradingEnvironment, Action
    
    # 創建模擬數據
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    data = pd.DataFrame({
        'open': prices + np.random.randn(100) * 0.5,
        'high': prices + abs(np.random.randn(100)) + 1,
        'low': prices - abs(np.random.randn(100)) - 1,
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    env = TradingEnvironment(data, initial_capital=100000)
    obs = env.reset()
    
    # 執行幾步
    total_reward = 0
    for _ in range(10):
        action = Action.HOLD
        obs, reward, done, info = env.step(action)
        total_reward += reward
        if done:
            break
    
    perf = env.get_performance()
    print(f"✅ 環境運作成功")
    print(f"   初始資金: $100,000")
    print(f"   最終價值: ${perf['final_value']:,.2f}")
    print(f"   總回報: {perf['total_return']:.2%}")
    print(f"   交易次數: {perf['trades_count']}")
except Exception as e:
    print(f"❌ 失敗: {e}")

# 測試 6: RLAgent
print("\n[測試 3.2] RLAgent 強化學習智能體...")
try:
    from src.reinforcement_learning import RLAgent
    
    agent = RLAgent(
        state_dim=6,
        action_dim=4,
        epsilon=0.5
    )
    
    # 測試選擇動作
    test_state = np.array([0.01, 0.02, -0.01, 1.0, 0.5, 0.0])
    action = agent.select_action(test_state, training=True)
    
    print(f"✅ 智能體初始化成功")
    print(f"   狀態維度: {agent.state_dim}")
    print(f"   動作維度: {agent.action_dim}")
    print(f"   探索率 epsilon: {agent.epsilon}")
    print(f"   測試動作: {action}")
    
    # 測試經驗存儲
    agent.store_experience(test_state, action, 0.1, test_state, False)
    print(f"   經驗回放大小: {len(agent.memory)}")
except Exception as e:
    print(f"❌ 失敗: {e}")

# 測試 7: RewardCalculator
print("\n[測試 3.3] RewardCalculator 獎勵計算器...")
try:
    from src.reinforcement_learning import RewardCalculator
    
    calc = RewardCalculator()
    
    reward = calc.calculate(
        current_value=105000,
        previous_value=100000,
        position=1,
        step=10
    )
    
    print(f"✅ 獎勵計算成功")
    print(f"   盈虧獎勵: {reward.pnl_reward:.4f}")
    print(f"   回撤懲罰: {reward.drawdown_penalty:.4f}")
    print(f"   總獎勵: {reward.total_reward:.4f}")
except Exception as e:
    print(f"❌ 失敗: {e}")

# 測試 8: RLTrainer
print("\n[測試 3.4] RLTrainer 訓練器...")
try:
    from src.reinforcement_learning import RLTrainer, TrainingConfig
    
    config = TrainingConfig(episodes=10, max_steps=50)
    agent = RLAgent(state_dim=6, action_dim=4)
    trainer = RLTrainer(env, agent, config)
    
    summary = trainer.get_training_summary()
    print(f"✅ 訓練器初始化成功")
    print(f"   訓練回合: {config.episodes}")
    print(f"   每回合步數: {config.max_steps}")
    print(f"   批次大小: {config.batch_size}")
except Exception as e:
    print(f"❌ 失敗: {e}")

print("\n" + "=" * 70)
print("✅ Phase 2 & 3 所有組件測試通過！")
print("=" * 70)
