#!/usr/bin/env python3
"""策略整合測試"""

import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot')

print('=' * 60)
print('策略整合測試')
print('=' * 60)

strategies = [
    ('trend_strategy', 'TrendStrategy'),
    ('tqqq_long_short', 'TQQQLongShortStrategy'),
    ('zscore_strategy', 'ZScoreStrategy'),
    ('breakout', 'BreakoutStrategy'),
    ('flexible_arbitrage', 'FlexibleArbitrageStrategy'),
    ('momentum', 'MomentumStrategy'),
    ('enhanced_strategy', 'EnhancedStrategy'),
]

all_passed = True

for module_name, class_name in strategies:
    print(f'\n📊 {class_name}')
    try:
        module = __import__(f'src.strategies.{module_name}', fromlist=[class_name])
        strategy_class = getattr(module, class_name)
        
        # 實例化
        instance = strategy_class()
        print(f'  實例化: ✅ 成功')
        
        # 檢查MTF
        has_mtf = hasattr(instance, 'mtf_analyzer') and instance.mtf_analyzer is not None
        mtf_status = '✅' if has_mtf else '❌'
        print(f'  MTF整合: {mtf_status}')
        
        # 檢查必要方法
        has_on_data = hasattr(instance, 'on_data')
        has_on_order = hasattr(instance, 'on_order_update')
        has_on_position = hasattr(instance, 'on_position_update')
        
        on_data_status = '✅' if has_on_data else '❌'
        on_order_status = '✅' if has_on_order else '❌'
        on_position_status = '✅' if has_on_position else '❌'
        
        print(f'  on_data: {on_data_status}')
        print(f'  on_order_update: {on_order_status}')
        print(f'  on_position_update: {on_position_status}')
        
        if not (has_on_data and has_on_order and has_on_position):
            all_passed = False
        
    except Exception as e:
        print(f'  ❌ 錯誤: {e}')
        all_passed = False

print('\n' + '=' * 60)
if all_passed:
    print('✅ 所有策略測試通過')
else:
    print('⚠️ 部分策略需要關注')
print('=' * 60)
