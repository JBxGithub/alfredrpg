"""
測試 NQmain 期貨主連
"""
import futu as ft

quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

# 各種可能的 NQmain 格式
test_codes = [
    'NQmain', 'US.NQmain', 'NQMAIN', 'US.NQMAIN',
    'NQMain', 'US.NQMain',
    'NQ', 'US.NQ',
    'MNQmain', 'US.MNQmain',
    'US.NQ1', 'NQ1',
    'US.NQ.MAIN', 'NQ.MAIN',
    # 期貨格式
    'CME.NQ', 'CME.MNQ',
    'GLOBEX.NQ', 'GLOBEX.MNQ',
]

print('測試 NQmain 期貨主連:')
for code in test_codes:
    try:
        ret, data = quote_ctx.get_market_snapshot([code])
        if ret == ft.RET_OK and not data.empty:
            name = data['name'].values[0]
            price = data['last_price'].values[0]
            print(f'  ✅ {code}: {name} - {price}')
        else:
            print(f'  ❌ {code}: ret={ret}')
    except Exception as e:
        print(f'  ❌ {code}: {str(e)[:40]}')

# 嘗試獲取期貨列表
print('\n嘗試獲取期貨數據:')
try:
    # 獲取美股期貨
    ret, data = quote_ctx.get_stock_basicinfo(ft.Market.US, 'FUTURE')
    if ret == ft.RET_OK and not data.empty:
        print(f'  找到 {len(data)} 個期貨')
        # 搜索 NQ
        nq_data = data[data['code'].str.contains('NQ', case=False, na=False)]
        if not nq_data.empty:
            print('  NQ 相關期貨:')
            for _, row in nq_data.head(10).iterrows():
                print(f'    {row["code"]}: {row["name"]}')
        else:
            print('  沒有找到 NQ 期貨')
    else:
        print(f'  無法獲取期貨列表: ret={ret}')
except Exception as e:
    print(f'  錯誤: {str(e)[:60]}')

quote_ctx.close()
