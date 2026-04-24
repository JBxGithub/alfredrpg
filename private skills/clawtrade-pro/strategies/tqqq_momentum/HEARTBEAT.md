# TQQQ Momentum Strategy - HEARTBEAT Configuration
# 在美股交易時間內每5分鐘檢查一次信號

## Market Hours Check (09:30-16:00 ET, Mon-Fri)

1. **Check TQQQ momentum signals every 5 minutes**
   - Run: `python ~/openclaw_workspace/skills/tqqq-momentum/strategy.py`
   - Or import and call: `run_strategy_check()`

2. **If signal generated (BUY/SELL/STRONG_BUY/STRONG_SLL):**
   - Check risk limits (max position size, stop loss)
   - If risk check passed, notify user via WhatsApp
   - Wait for user confirmation before executing

3. **Risk Check Items:**
   - Current position size < max_position_size (25%)
   - Daily loss < max_daily_loss_pct (2%)
   - Current drawdown < max_drawdown_pct (15%)
   - Not in cooldown period

4. **Notification Format:**
   ```
   🚨 TQQQ 交易信號
   
   信號: BUY (強)
   當前價: $52.35
   RSI: 28.5 (超賣)
   MA20: $51.80 > MA50: $52.10
   MACD: 0.15 > Signal: 0.08
   
   建議: 買入 100 股
   止損: $49.73 (-5%)
   止盈: $57.59 (+10%)
   
   回覆 /confirm 執行 或 /ignore 忽略
   ```

## Pre-Market Check (04:00-09:30 ET)
- Light monitoring only
- No trading signals
- Prepare daily analysis

## After-Hours Check (16:00-20:00 ET)
- Daily summary
- Position review
- Next day preparation

## Weekend Check (Sat-Sun)
- Weekly performance review
- Strategy parameter optimization
- Market news analysis
