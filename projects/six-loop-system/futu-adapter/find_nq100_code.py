"""
查找正確的 NQ 100 指數代碼
測試各種可能的代碼格式
"""

import futu as ft
from datetime import datetime

def test_code(quote_ctx, code):
    """測試單個代碼"""
    try:
        ret, data = quote_ctx.get_market_snapshot([code])
        if ret == ft.RET_OK and not data.empty:
            print(f"  ✅ {code}: {data['name'].values[0]} - 價格: {data['last_price'].values[0]}")
            return True
        else:
            print(f"  ❌ {code}: 無數據")
            return False
    except Exception as e:
        print(f"  ❌ {code}: {str(e)[:50]}")
        return False

def find_nq100():
    """查找 NQ 100 指數"""
    print("=" * 60)
    print("查找 NQ 100 指數代碼")
    print("=" * 60)
    
    # 連接 OpenD
    quote_ctx = ft.OpenQuoteContext(host="127.0.0.1", port=11111)
    
    # 測試各種可能的代碼
    test_codes = [
        # 指數
        "US.NDX", "US.NDX100", "US.NASDAQ100",
        "US.IXIC",  # Nasdaq Composite
        "US.QQQ",   # QQQ ETF (最接近 NQ 100)
        
        # 期貨
        "US.NQ", "US.MNQ", "US.NQMAIN",
        
        # 其他格式
        "NDX", "NASDAQ100", "QQQ",
    ]
    
    print("\n測試指數代碼:")
    for code in test_codes:
        test_code(quote_ctx, code)
    
    # 嘗試搜索
    print("\n搜索 Nasdaq 相關:")
    try:
        ret, data = quote_ctx.search_stock("NASDAQ")
        if ret == ft.RET_OK and not data.empty:
            print(f"  找到 {len(data)} 個結果:")
            for _, row in data.head(10).iterrows():
                print(f"    {row['code']}: {row['name']}")
    except Exception as e:
        print(f"  搜索失敗: {e}")
    
    # 搜索 NDX
    print("\n搜索 NDX:")
    try:
        ret, data = quote_ctx.search_stock("NDX")
        if ret == ft.RET_OK and not data.empty:
            print(f"  找到 {len(data)} 個結果:")
            for _, row in data.head(10).iterrows():
                print(f"    {row['code']}: {row['name']}")
    except Exception as e:
        print(f"  搜索失敗: {e}")
    
    # 搜索 QQQ
    print("\n搜索 QQQ:")
    try:
        ret, data = quote_ctx.search_stock("QQQ")
        if ret == ft.RET_OK and not data.empty:
            print(f"  找到 {len(data)} 個結果:")
            for _, row in data.head(10).iterrows():
                print(f"    {row['code']}: {row['name']}")
    except Exception as e:
        print(f"  搜索失敗: {e}")
    
    quote_ctx.close()
    
    print("\n" + "=" * 60)
    print("結論: 使用 US.QQQ 作為 NQ 100 的代理")
    print("QQQ 是 Invesco QQQ Trust，追蹤 NQ 100 指數")
    print("=" * 60)

if __name__ == '__main__':
    find_nq100()
