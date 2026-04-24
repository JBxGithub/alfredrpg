"""
嘗試各種方法獲取 NDX 數據
"""
import futu as ft

quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

print('嘗試各種 NDX 獲取方法:')

# 方法 1: 直接獲取快照
print('\n1. 直接獲取市場快照:')
test_codes = ['.NDX', 'NDX', 'US.NDX', 'IXIC', 'US.IXIC', 'NASDAQ', 'US.NASDAQ']
for code in test_codes:
    try:
        ret, data = quote_ctx.get_market_snapshot([code])
        if ret == ft.RET_OK and not data.empty:
            print(f'  ✅ {code}: {data["name"].values[0]} - {data["last_price"].values[0]}')
        else:
            print(f'  ❌ {code}: ret={ret}')
    except Exception as e:
        print(f'  ❌ {code}: {str(e)[:40]}')

# 方法 2: 嘗試訂閱
print('\n2. 嘗試訂閱:')
for code in ['.NDX', 'US.NDX']:
    try:
        ret, err = quote_ctx.subscribe(code, [ft.SubType.QUOTE])
        if ret == ft.RET_OK:
            print(f'  ✅ {code}: 訂閱成功')
        else:
            print(f'  ❌ {code}: {err}')
    except Exception as e:
        print(f'  ❌ {code}: {str(e)[:40]}')

# 方法 3: 獲取股票基本信息
print('\n3. 獲取股票基本信息:')
for code in ['.NDX', 'US.NDX']:
    try:
        ret, data = quote_ctx.get_stock_basicinfo(ft.Market.US, code)
        if ret == ft.RET_OK and not data.empty:
            print(f'  ✅ {code}: {data}')
        else:
            print(f'  ❌ {code}: ret={ret}')
    except Exception as e:
        print(f'  ❌ {code}: {str(e)[:40]}')

# 方法 4: 獲取實時報價
print('\n4. 獲取實時報價:')
for code in ['.NDX', 'US.NDX']:
    try:
        ret, data = quote_ctx.get_stock_quote(code)
        if ret == ft.RET_OK and not data.empty:
            print(f'  ✅ {code}: {data}')
        else:
            print(f'  ❌ {code}: ret={ret}')
    except Exception as e:
        print(f'  ❌ {code}: {str(e)[:40]}')

# 方法 5: 獲取 K 線
print('\n5. 獲取 K 線數據:')
for code in ['.NDX', 'US.NDX']:
    try:
        ret, data = quote_ctx.get_cur_kline(code, num=1, ktype=ft.KLType.K_DAY)
        if ret == ft.RET_OK and not data.empty:
            print(f'  ✅ {code}: {data}')
        else:
            print(f'  ❌ {code}: ret={ret}')
    except Exception as e:
        print(f'  ❌ {code}: {str(e)[:40]}')

quote_ctx.close()

print('\n結論: 如果以上方法都失敗，則 OpenD API 無法訪問 NDX')
print('必須使用 QQQ 作為代理，或通過其他數據源獲取 NDX')
