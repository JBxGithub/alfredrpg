"""
測試 MNQmain 和 NQ 期貨
"""
import futu as ft

quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

# 找到的正確代碼
test_codes = [
    'US.MNQmain',      # Micro E-mini Nasdaq-100 Index Futures (JUN6)
    'US.MNQcurrent',   # Micro E-mini Nasdaq-100 Index Futures Current Contract
    'US.NQ2606',       # E-mini NASDAQ 100 JUN6
    'US.MNQ2606',      # Micro E-mini Nasdaq-100 Index JUN6
]

print('測試 MNQmain / NQ 期貨:')
for code in test_codes:
    try:
        ret, data = quote_ctx.get_market_snapshot([code])
        if ret == ft.RET_OK and not data.empty:
            name = data['name'].values[0]
            price = data['last_price'].values[0]
            high = data['high_price'].values[0]
            low = data['low_price'].values[0]
            volume = data['volume'].values[0]
            print(f'\n  ✅ {code}')
            print(f'     名稱: {name}')
            print(f'     價格: {price}')
            print(f'     最高: {high}')
            print(f'     最低: {low}')
            print(f'     成交量: {volume}')
        else:
            print(f'  ❌ {code}: ret={ret}')
    except Exception as e:
        print(f'  ❌ {code}: {str(e)[:60]}')

quote_ctx.close()
