import futu as ft
import os

host = os.getenv('FUTU_HOST', '127.0.0.1')
port = int(os.getenv('FUTU_PORT', '11111'))

print('=== Futu API 賬戶檢查 ===')
print(f'連接: {host}:{port}')

# 測試行情連接
quote_ctx = ft.OpenQuoteContext(host=host, port=port)
ret, data = quote_ctx.get_global_state()
if ret == ft.RET_OK:
    print('✅ 行情 API: 已連接')
else:
    print(f'❌ 行情 API: 失敗 - {data}')
quote_ctx.close()

# 測試美股交易連接 (保證金賬戶)
print('\n=== 美股保證金賬戶 ===')
trade_ctx = ft.OpenSecTradeContext(filter_trdmarket=ft.TrdMarket.US, host=host, port=port)

# 檢查賬戶資金 (真實賬戶)
ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)
if ret == ft.RET_OK:
    print('✅ 真實賬戶已連接')
    if len(data) > 0:
        total_assets = data['total_assets'].values[0] if 'total_assets' in data.columns else 'N/A'
        available = data['available_funds'].values[0] if 'available_funds' in data.columns else 'N/A'
        print(f'   總資產: {total_assets}')
        print(f'   可用現金: {available}')
else:
    print(f'❌ 真實賬戶: {ret} - {data}')

# 檢查持倉
ret, positions = trade_ctx.position_list_query(trd_env=ft.TrdEnv.REAL)
if ret == ft.RET_OK:
    print(f'✅ 持倉查詢成功: {len(positions)} 個持倉')
else:
    print(f'持倉查詢: {ret} - {positions}')

trade_ctx.close()

# 檢查期貨賬戶
print('\n=== 期貨賬戶 ===')
try:
    fut_ctx = ft.OpenFutureTradeContext(host=host, port=port)
    ret, data = fut_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)
    if ret == ft.RET_OK:
        print('✅ 期貨賬戶已連接')
        if len(data) > 0:
            total = data['total_assets'].values[0] if 'total_assets' in data.columns else 'N/A'
            print(f'   總資產: {total}')
    else:
        print(f'❌ 期貨賬戶: {ret} - {data}')
    fut_ctx.close()
except Exception as e:
    print(f'期貨賬戶檢查失敗: {e}')

print('\n=== 檢查完成 ===')
