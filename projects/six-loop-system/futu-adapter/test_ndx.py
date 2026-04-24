"""
測試 .NDX 代碼
"""
import futu as ft

quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

# 測試各種 NDX 格式
codes = ['.NDX', 'US.NDX', 'NDX', 'US.QQQ', 'NDX.US']

print('測試 NQ 100 代碼:')
for code in codes:
    try:
        ret, data = quote_ctx.get_market_snapshot([code])
        if ret == ft.RET_OK and not data.empty:
            name = data['name'].values[0]
            price = data['last_price'].values[0]
            print(f'  ✅ {code}: {name} - 價格: {price}')
        else:
            print(f'  ❌ {code}: 無數據 (ret={ret})')
    except Exception as e:
        print(f'  ❌ {code}: {str(e)[:50]}')

quote_ctx.close()
