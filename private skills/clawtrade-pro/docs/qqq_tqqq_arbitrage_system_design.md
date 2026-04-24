# QQQ/TQQQ 統計套利交易系統設計

## 1. 策略原理

### 1.1 理論關係
- **TQQQ** 是 **QQQ** 的 3 倍日內槓桿 ETF
- 理論價格關係：TQQQ ≈ QQQ × 3（考慮費用和複利效應）
- 實際關係：TQQQ = QQQ³ × (1 - 費用率)^t × 複利調整因子

### 1.2 套利邏輯
當 TQQQ 價格偏離理論價值時：
- **TQQQ 過高**：賣 TQQQ，買 QQQ（對沖）
- **TQQQ 過低**：買 TQQQ，賣 QQQ（對沖）

### 1.3 價差計算
```
理論 TQQQ 價格 = (QQQ_price / QQQ_baseline)³ × TQQQ_baseline × 衰減因子
價差 = TQQQ_actual - TQQQ_theoretical
價差比率 = 價差 / TQQQ_theoretical
```

## 2. 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                    QQQ/TQQQ 套利系統                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   數據收集    │───►│   信號生成    │───►│   交易執行    │  │
│  │  (Futu API)  │    │  (價差計算)   │    │  (雙向下單)   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    風控系統                           │  │
│  │  (保證金監控、回撤控制、異常處理)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                               │
│                            ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   監控儀表板                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 3. 核心模塊設計

### 3.1 數據收集模塊
```python
class DataCollector:
    """實時數據收集"""
    
    def __init__(self, host='127.0.0.1', port=11111):
        self.quote_ctx = ft.OpenQuoteContext(host, port)
        self.subscribed = False
    
    def subscribe_quotes(self):
        """訂閱 QQQ 和 TQQQ 實時報價"""
        ret1, _ = self.quote_ctx.subscribe(['QQQ'], [ft.SubType.QUOTE])
        ret2, _ = self.quote_ctx.subscribe(['TQQQ'], [ft.SubType.QUOTE])
        self.subscribed = (ret1 == ft.RET_OK and ret2 == ft.RET_OK)
        return self.subscribed
    
    def get_prices(self):
        """獲取當前價格"""
        ret1, qqq_data = self.quote_ctx.get_market_snapshot(['QQQ'])
        ret2, tqqq_data = self.quote_ctx.get_market_snapshot(['TQQQ'])
        
        if ret1 == ft.RET_OK and ret2 == ft.RET_OK:
            return {
                'QQQ': qqq_data['last_price'][0],
                'TQQQ': tqqq_data['last_price'][0],
                'timestamp': datetime.now()
            }
        return None
```

### 3.2 信號生成模塊
```python
class SignalGenerator:
    """套利信號生成"""
    
    def __init__(self, baseline_qqq=400.0, baseline_tqqq=40.0):
        self.baseline_qqq = baseline_qqq
        self.baseline_tqqq = baseline_tqqq
        self.decay_factor = 0.9995  # 每日衰減因子（考慮費用）
        self.threshold = 0.005  # 0.5% 閾值
    
    def calculate_theoretical_tqqq(self, qqq_price):
        """計算理論 TQQQ 價格"""
        ratio = qqq_price / self.baseline_qqq
        theoretical = (ratio ** 3) * self.baseline_tqqq * self.decay_factor
        return theoretical
    
    def generate_signal(self, qqq_price, tqqq_price):
        """生成交易信號"""
        theoretical = self.calculate_theoretical_tqqq(qqq_price)
        spread = tqqq_price - theoretical
        spread_ratio = spread / theoretical
        
        if spread_ratio > self.threshold:
            return {
                'signal': 'SELL_TQQQ_BUY_QQQ',
                'spread_ratio': spread_ratio,
                'theoretical': theoretical,
                'strength': abs(spread_ratio) / self.threshold
            }
        elif spread_ratio < -self.threshold:
            return {
                'signal': 'BUY_TQQQ_SELL_QQQ',
                'spread_ratio': spread_ratio,
                'theoretical': theoretical,
                'strength': abs(spread_ratio) / self.threshold
            }
        return {'signal': 'HOLD', 'spread_ratio': spread_ratio}
```

### 3.3 交易執行模塊
```python
class TradeExecutor:
    """交易執行"""
    
    def __init__(self, host='127.0.0.1', port=11111):
        self.trade_ctx = ft.OpenSecTradeContext(
            filter_trdmarket=ft.TrdMarket.US,
            host=host, port=port
        )
        self.position_ratio = 0.3  # 單筆使用 30% 資金
    
    def execute_arbitrage(self, signal, qqq_price, tqqq_price, total_funds):
        """執行套利交易"""
        position_value = total_funds * self.position_ratio
        
        if signal['signal'] == 'SELL_TQQQ_BUY_QQQ':
            # 賣 TQQQ，買 QQQ
            tqqq_qty = int(position_value / 2 / tqqq_price)
            qqq_qty = int(position_value / 2 / qqq_price)
            
            self.place_order('TQQQ', ft.TrdSide.SELL, tqqq_qty)
            self.place_order('QQQ', ft.TrdSide.BUY, qqq_qty)
            
        elif signal['signal'] == 'BUY_TQQQ_SELL_QQQ':
            # 買 TQQQ，賣 QQQ
            tqqq_qty = int(position_value / 2 / tqqq_price)
            qqq_qty = int(position_value / 2 / qqq_price)
            
            self.place_order('TQQQ', ft.TrdSide.BUY, tqqq_qty)
            self.place_order('QQQ', ft.TrdSide.SELL, qqq_qty)
    
    def place_order(self, symbol, side, qty):
        """下單"""
        ret, data = self.trade_ctx.place_order(
            price=0.0,  # 市價單
            qty=qty,
            code=symbol,
            trd_side=side,
            order_type=ft.OrderType.MARKET,
            trd_env=ft.TrdEnv.REAL
        )
        return ret == ft.RET_OK
```

### 3.4 風控模塊
```python
class RiskManager:
    """風險管理"""
    
    def __init__(self):
        self.max_daily_loss = 500  # 日虧損上限 $500
        self.max_drawdown = 0.05   # 最大回撤 5%
        self.max_positions = 2     # 最大持倉數
        self.current_pnl = 0
        self.daily_pnl = 0
    
    def check_risk(self, signal, positions, funds):
        """檢查風險"""
        # 檢查日虧損
        if self.daily_pnl < -self.max_daily_loss:
            return False, 'Daily loss limit reached'
        
        # 檢查持倉數
        if len(positions) >= self.max_positions:
            return False, 'Max positions reached'
        
        # 檢查保證金
        if funds['available'] < funds['total'] * 0.3:  # 保留 30% 現金
            return False, 'Insufficient margin buffer'
        
        return True, 'OK'
    
    def update_pnl(self, pnl):
        """更新盈虧"""
        self.current_pnl += pnl
        self.daily_pnl += pnl
```

## 4. 主程序流程

```python
class QQQTQQQArbitrageSystem:
    """主系統"""
    
    def __init__(self):
        self.data_collector = DataCollector()
        self.signal_generator = SignalGenerator()
        self.trade_executor = TradeExecutor()
        self.risk_manager = RiskManager()
        self.running = False
    
    def start(self):
        """啟動系統"""
        self.running = True
        self.data_collector.subscribe_quotes()
        
        while self.running:
            try:
                # 1. 獲取價格
                prices = self.data_collector.get_prices()
                if not prices:
                    continue
                
                # 2. 生成信號
                signal = self.signal_generator.generate_signal(
                    prices['QQQ'], prices['TQQQ']
                )
                
                # 3. 檢查風險
                funds = self.get_funds()
                positions = self.get_positions()
                can_trade, reason = self.risk_manager.check_risk(
                    signal, positions, funds
                )
                
                # 4. 執行交易
                if can_trade and signal['signal'] != 'HOLD':
                    self.trade_executor.execute_arbitrage(
                        signal, prices['QQQ'], prices['TQQQ'], funds['total']
                    )
                
                # 5. 等待下一週期
                time.sleep(5)  # 5 秒檢查一次
                
            except Exception as e:
                logger.error(f'Error: {e}')
                time.sleep(10)
    
    def stop(self):
        """停止系統"""
        self.running = False
```

## 5. 回測方案

```python
class Backtester:
    """回測系統"""
    
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.trades = []
        self.pnl_history = []
    
    def run_backtest(self, data):
        """運行回測"""
        signal_gen = SignalGenerator()
        
        for i, row in data.iterrows():
            signal = signal_gen.generate_signal(row['QQQ'], row['TQQQ'])
            
            if signal['signal'] != 'HOLD':
                # 模擬交易
                trade = self.simulate_trade(signal, row)
                self.trades.append(trade)
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        """計算回測指標"""
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        total_pnl = sum([t['pnl'] for t in self.trades])
        
        return {
            'total_trades': total_trades,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / total_trades if total_trades > 0 else 0
        }
```

## 6. 實施時間表

| 週數 | 任務 |
|------|------|
| 第 1 週 | 完成核心模塊開發 |
| 第 2 週 | 回測和參數優化 |
| 第 3 週 | 模擬交易測試 |
| 第 4 週 | 小資金實盤上線 |

## 7. 風險提示

1. **槓桿風險**：TQQQ 是 3 倍槓桿，波動較大
2. **流動性風險**：確保兩者都有足夠流動性
3. **保證金風險**：監控保證金水平，避免追繳
4. **系統風險**：API 故障或延遲可能導致損失

## 8. 預期收益

- **保守估計**：年化 10-20%
- **夏普比率**：1.2-1.8
- **最大回撤**：< 8%
