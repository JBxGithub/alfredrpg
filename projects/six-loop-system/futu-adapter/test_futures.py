"""
測試納斯達克期貨代碼
"""
import futu as ft

quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

# 測試各種期貨代碼
futures_codes = [
    # 納斯達克期貨
    'NQmain', 'US.NQmain', 'NQMAIN', 'US.NQMAIN',
    'MNQmain', 'US.MNQmain', 'MNQMAIN', 'US.MNQMAIN',
    # 標準格式
    'NQ', 'US.NQ',
    'MNQ', 'US.MNQ',
    # 其他可能格式
    'US.NQ1!', 'NQ1!',
    'US.MNQ1!', 'MNQ1!',
    # 對比
    'US.QQQ'
]

print('測試納斯達克期貨代碼:')
for code in futures_codes:
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
