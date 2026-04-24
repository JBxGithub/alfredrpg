"""
測試 NQ100 數據獲取（不連接數據庫）
"""

import sys
sys.path.insert(0, '.')

from nq100_constituents import NQ100Fetcher

print("=" * 60)
print("測試 NQ100 成份股獲取")
print("=" * 60)

fetcher = NQ100Fetcher()

# 1. 獲取所有成份股
print("\n1. 獲取成份股列表...")
constituents = fetcher.fetch_constituents()
print(f"   ✅ 成功獲取 {len(constituents)} 隻成份股")

# 2. 計算權重
print("\n2. 計算權重（基於市值）...")
constituents = fetcher.calculate_weights(constituents)
print(f"   ✅ 完成權重計算")

# 3. 取前50
print("\n3. 提取前50隻...")
top_50 = fetcher.get_top_n(constituents, 50)
print(f"   ✅ 提取前 {len(top_50)} 隻")

# 顯示結果
print("\n" + "=" * 60)
print("前20大成份股:")
print("=" * 60)
for i, c in enumerate(top_50[:20], 1):
    weight_str = f"{c['weight']:.2f}%" if c['weight'] > 0 else "N/A"
    market_cap = c.get('market_cap', 0)
    if market_cap:
        market_cap_str = f"${market_cap/1e12:.2f}T" if market_cap >= 1e12 else f"${market_cap/1e9:.2f}B"
    else:
        market_cap_str = "N/A"
    print(f"{i:2d}. {c['symbol']:6s} - {c['name'][:35]:35s} - 權重: {weight_str:6s} - 市值: {market_cap_str}")

print("\n" + "=" * 60)
print(f"總計: 成功獲取 {len(constituents)} 隻，提取前 {len(top_50)} 隻")
print("=" * 60)
