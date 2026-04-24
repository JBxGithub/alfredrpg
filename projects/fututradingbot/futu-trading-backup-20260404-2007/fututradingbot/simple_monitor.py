# 簡化版交易監控腳本
# 直接顯示真實帳戶數據

import asyncio
import json
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.api.futu_client import FutuTradeClient, Market, TrdEnv

async def monitor_account():
    """監控真實帳戶數據"""
    print("=" * 60)
    print("FutuTradingBot 真實帳戶監控")
    print("=" * 60)
    
    # 連接交易客戶端
    trade_client = FutuTradeClient(host="127.0.0.1", port=11111, market=Market.US)
    
    if not trade_client.connect():
        print("❌ 無法連接交易客戶端")
        return
    
    print("✅ 已連接富途交易接口")
    
    # 解鎖交易
    if trade_client.unlock_trade("011087"):
        print("✅ 交易接口已解鎖")
    else:
        print("⚠️ 交易接口解鎖失敗")
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # 查詢帳戶資金
            ret_code, account_data = trade_client.accinfo_query(TrdEnv.REAL)
            
            if ret_code == 0 and account_data is not None:
                print(f"\n📊 帳戶資金 (REAL):")
                print(f"   原始數據: {account_data}")
                
                # 嘗試解析數據
                if hasattr(account_data, 'to_dict'):
                    data_list = account_data.to_dict('records')
                    if len(data_list) > 0:
                        data = data_list[0]
                        print(f"\n   解析後數據:")
                        for key, value in data.items():
                            print(f"      {key}: {value}")
            else:
                print(f"❌ 無法獲取帳戶資金: ret_code={ret_code}")
            
            # 查詢持倉
            ret_code, positions = trade_client.position_list_query(TrdEnv.REAL)
            
            if ret_code == 0 and positions is not None:
                print(f"\n📈 持倉列表:")
                if hasattr(positions, 'to_dict'):
                    pos_list = positions.to_dict('records')
                    if len(pos_list) > 0:
                        for pos in pos_list:
                            print(f"   {pos.get('code', 'N/A')}: {pos.get('qty', 0)}股 @ ${pos.get('nominal_price', 0)}")
                    else:
                        print("   無持倉")
                else:
                    print(f"   數據: {positions}")
            else:
                print(f"❌ 無法獲取持倉: ret_code={ret_code}")
            
            # 查詢今日訂單
            ret_code, orders = trade_client.order_list_query(TrdEnv.REAL)
            
            if ret_code == 0 and orders is not None:
                print(f"\n📝 今日訂單:")
                if hasattr(orders, 'to_dict'):
                    order_list = orders.to_dict('records')
                    today = datetime.now().strftime('%Y-%m-%d')
                    today_orders = [o for o in order_list if today in str(o.get('create_time', ''))]
                    
                    if len(today_orders) > 0:
                        for order in today_orders[:5]:  # 只顯示最近5筆
                            print(f"   {order.get('code', 'N/A')} {order.get('trd_side', 'N/A')} {order.get('qty', 0)}@{order.get('price', 0)}")
                    else:
                        print("   今日無訂單")
                else:
                    print(f"   數據: {orders}")
            else:
                print(f"❌ 無法獲取訂單: ret_code={ret_code}")
            
            print(f"\n{'='*60}")
            print("等待 10 秒後更新...")
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n監控已停止")
    finally:
        trade_client.close()
        print("已斷開連接")

if __name__ == "__main__":
    asyncio.run(monitor_account())
