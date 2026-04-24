# 緊急清倉腳本
# 立即清倉所有持倉

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.futu_client import FutuTradeClient, Market, TrdEnv, TrdSide, OrderType

def emergency_close_all():
    """緊急清倉所有持倉"""
    print("=" * 60)
    print("🚨 緊急清倉模式")
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
        print("❌ 交易接口解鎖失敗")
        return
    
    # 查詢持倉
    ret_code, positions = trade_client.position_list_query(TrdEnv.REAL)
    
    if ret_code == 0 and positions is not None:
        if hasattr(positions, 'to_dict'):
            pos_list = positions.to_dict('records')
        else:
            pos_list = list(positions) if positions else []
        
        if len(pos_list) == 0:
            print("✅ 無持倉需要清倉")
            return
        
        print(f"\n📊 發現 {len(pos_list)} 個持倉，開始清倉...")
        
        for pos in pos_list:
            if isinstance(pos, dict):
                code = pos.get('code', '')
                qty = int(pos.get('qty', 0))
                side = pos.get('position_side', 'LONG')
                
                if qty > 0:
                    # 決定交易方向
                    if side == 'LONG':
                        trd_side = TrdSide.SELL
                        action = "賣出"
                    else:
                        trd_side = TrdSide.BUY
                        action = "買入平倉"
                    
                    print(f"\n   {action} {code}: {qty}股")
                    
                    # 下單清倉
                    ret, data = trade_client.place_order(
                        price=0,  # 市價單
                        qty=qty,
                        code=code,
                        trd_side=trd_side,
                        order_type=OrderType.MARKET,
                        trd_env=TrdEnv.REAL
                    )
                    
                    if ret == 0:
                        print(f"   ✅ 清倉成功")
                    else:
                        print(f"   ❌ 清倉失敗: {data}")
        
        print("\n" + "=" * 60)
        print("清倉完成")
        print("=" * 60)
    else:
        print(f"❌ 無法獲取持倉: ret_code={ret_code}")
    
    trade_client.close()

if __name__ == "__main__":
    emergency_close_all()
