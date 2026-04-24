"""
嘗試訂閱 MNQmain
"""
import futu as ft
import time

quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

# 嘗試訂閱 MNQmain
code = 'US.MNQmain'

print(f'嘗試訂閱 {code}...')
try:
    ret, err = quote_ctx.subscribe(code, [ft.SubType.QUOTE])
    if ret == ft.RET_OK:
        print(f'✅ 訂閱成功: {code}')
        
        # 獲取報價
        ret, data = quote_ctx.get_stock_quote([code])
        if ret == ft.RET_OK and not data.empty:
            print(f'數據: {data}')
        else:
            print(f'無法獲取報價: ret={ret}')
    else:
        print(f'❌ 訂閱失敗: {err}')
except Exception as e:
    print(f'❌ 錯誤: {e}')

quote_ctx.close()
