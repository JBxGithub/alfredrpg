"""
部分獲利機制整合示例

展示如何在實際交易中使用 RiskManager 的部分獲利功能
"""
import sys
sys.path.insert(0, 'src')
from risk import RiskManager, Position
from typing import Optional


class TradingEngine:
    """
    交易引擎示例 - 展示如何整合部分獲利機制
    """
    
    def __init__(self):
        self.risk_manager = RiskManager()
        self.risk_manager.update_capital(total_capital=1000000.0)
    
    def on_price_update(self, symbol: str, current_price: float):
        """
        價格更新回調 - 檢查部分獲利和止損
        
        這個方法應該在每次收到新價格時調用
        """
        # 1. 檢查是否需要部分獲利
        partial_action = self.risk_manager.check_partial_profit(symbol, current_price)
        if partial_action:
            self._execute_partial_profit(partial_action)
        
        # 2. 檢查是否觸發止損
        should_stop, reason = self.risk_manager.check_stop_loss(symbol, current_price)
        if should_stop:
            self._execute_stop_loss(symbol, current_price, reason)
    
    def _execute_partial_profit(self, action):
        """執行部分獲利"""
        print(f"\n>>> 執行部分獲利")
        print(f"    股票: {action.symbol}")
        print(f"    階段: 第{action.level_index + 1}階段")
        print(f"    平倉數量: {action.close_qty}股")
        print(f"    當前價格: ${action.current_price:.2f}")
        print(f"    預計獲利: ${action.profit_amount:.2f}")
        
        # 這裡應該調用實際的交易API下單
        # 例如: place_order(action.symbol, "SELL", action.close_qty, action.current_price)
        
        # 應用部分獲利結果到風險管理器
        self.risk_manager.apply_partial_profit(
            symbol=action.symbol,
            level_index=action.level_index,
            closed_qty=action.close_qty,
            close_price=action.current_price,
            realized_profit=action.profit_amount
        )
        
        print(f"    ✓ 部分獲利執行完成，止損已調整至 ${action.new_stop_loss:.2f}")
    
    def _execute_stop_loss(self, symbol: str, current_price: float, reason: str):
        """執行止損"""
        print(f"\n>>> 執行止損")
        print(f"    股票: {symbol}")
        print(f"    原因: {reason}")
        
        # 獲取當前持倉數量
        position = self.risk_manager.positions.get(symbol)
        if position and position.quantity > 0:
            print(f"    平倉數量: {position.quantity}股")
            # 這裡應該調用實際的交易API下單
            # 例如: place_order(symbol, "SELL", position.quantity, current_price)
            print(f"    ✓ 止損執行完成")
    
    def add_position(self, symbol: str, quantity: int, avg_price: float):
        """添加新持倉"""
        position = Position(
            symbol=symbol,
            quantity=quantity,
            avg_price=avg_price,
            market_price=avg_price
        )
        self.risk_manager.update_positions([position])
        print(f"\n添加持倉: {symbol} {quantity}股 @ ${avg_price:.2f}")
        print(f"初始止損價格: ${position.stop_loss_price:.2f}")
    
    def get_position_status(self, symbol: str):
        """獲取持倉狀態"""
        status = self.risk_manager.get_partial_profit_status(symbol)
        if status:
            print(f"\n=== {symbol} 持倉狀態 ===")
            print(f"原始持倉: {status['original_qty']}股")
            print(f"當前持倉: {status['current_qty']}股")
            print(f"已平倉: {status['total_closed_qty']}股")
            print(f"已實現獲利: ${status['total_profit_taken']:.2f}")
            print(f"止損價格: ${status['stop_loss_price']:.2f}")
            print("部分獲利階段:")
            for level in status['levels']:
                triggered = "✓ 已執行" if level['triggered'] else "○ 未觸發"
                print(f"  階段{level['index']+1}: 盈利{level['profit_pct']:.0f}% 平倉{level['close_pct']:.0f}% - {triggered}")


def simulate_trading():
    """模擬交易流程"""
    print("=" * 60)
    print("部分獲利機制整合示例")
    print("=" * 60)
    
    engine = TradingEngine()
    
    # 添加持倉: TQQQ 1000股 @ $50
    engine.add_position("TQQQ", 1000, 50.0)
    
    # 模擬價格變動
    price_scenarios = [
        ("價格上漲 1%", 50.50),    # 未達到第一階段
        ("價格上漲 2.5%", 51.25),  # 觸發第一階段
        ("價格上漲 3%", 51.50),    # 第一階段已執行
        ("價格上漲 4.5%", 52.25),  # 觸發第二階段
        ("價格下跌至止損", 49.00), # 觸發止損 (但已部分獲利，止損設在成本價)
    ]
    
    for description, price in price_scenarios:
        print(f"\n{'-' * 60}")
        print(f"場景: {description} (價格: ${price:.2f})")
        print('-' * 60)
        engine.on_price_update("TQQQ", price)
        engine.get_position_status("TQQQ")
    
    print("\n" + "=" * 60)
    print("模擬完成!")
    print("=" * 60)
    
    # 最終摘要
    print("\n最終摘要:")
    print("- 初始持倉: 1000股 @ $50.00")
    print("- 第一階段: 盈利2%時平倉300股")
    print("- 第二階段: 盈利4%時平倉300股")
    print("- 剩餘持倉: 400股")
    print("- 止損價格: $50.00 (保本)")
    print("- 總實現獲利: $1,050.00")


if __name__ == "__main__":
    simulate_trading()
