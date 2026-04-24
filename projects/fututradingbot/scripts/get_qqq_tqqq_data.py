import futu as ft
import pandas as pd
from datetime import datetime, timedelta

# 連接 Futu API
quote_ctx = ft.OpenQuoteContext('127.0.0.1', 11111)

# 獲取 QQQ 和 TQQQ 的歷史K線數據（60天）
end_date = datetime.now()
start_date = end_date - timedelta(days=60)

print('=== 獲取 QQQ 歷史數據 ===')
ret_qqq, qqq_data, next_page_req_key = quote_ctx.request_history_kline('US.QQQ', start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), ktype=ft.KLType.K_DAY)
if ret_qqq == ft.RET_OK:
    print(f'獲取到 {len(qqq_data)} 天數據')
    print(qqq_data[['time_key', 'close']].head(10))
    qqq_data.to_csv('qqq_history.csv', index=False)
    print('已保存到 qqq_history.csv')
else:
    print(f'錯誤: {qqq_data}')

print('\n=== 獲取 TQQQ 歷史數據 ===')
ret_tqqq, tqqq_data, next_page_req_key2 = quote_ctx.request_history_kline('US.TQQQ', start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), ktype=ft.KLType.K_DAY)
if ret_tqqq == ft.RET_OK:
    print(f'獲取到 {len(tqqq_data)} 天數據')
    print(tqqq_data[['time_key', 'close']].head(10))
    tqqq_data.to_csv('tqqq_history.csv', index=False)
    print('已保存到 tqqq_history.csv')
else:
    print(f'錯誤: {tqqq_data}')

quote_ctx.close()
print('\n=== 數據獲取完成 ===')
