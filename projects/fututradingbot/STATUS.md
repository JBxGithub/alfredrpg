# FutuTradingBot Status

## Last Updated: 2026-03-27

## System Status: ✅ OPERATIONAL

### Components

#### 1. Realtime Bridge (src/realtime_bridge.py)
- **Status**: Running
- **Port**: ws://127.0.0.1:8765
- **Function**: Connects to Futu API, fetches real-time TQQQ/SQQQ prices, calculates trading signals
- **Connection**: Connected to Futu OpenD at 127.0.0.1:11111

#### 2. Dashboard (src/dashboard/app.py)
- **Status**: Running
- **URL**: http://127.0.0.1:8080
- **Password**: futu2024
- **Function**: Web UI for monitoring prices, account, positions, and trading signals

### Features Implemented

1. **Real-time Price Display**
   - TQQQ: Live price with change % and volume
   - SQQQ: Live price with change % and volume
   - Updates every 2 seconds

2. **Account Summary**
   - Total Assets
   - Available Cash
   - Daily P&L
   - Unrealized P&L

3. **Trading Signals (Z-Score Strategy)**
   - Calculates z-score based on TQQQ/SQQQ price ratio
   - Generates BUY signals when z-score < -2.0 (TQQQ undervalued)
   - Generates SELL signals when z-score > 2.0 (TQQQ overvalued)
   - Shows confidence level and reason

4. **Manual Trading**
   - Buy/Sell buttons for manual order entry
   - Emergency close all positions
   - Strategy toggle (start/stop)

5. **Activity Logging**
   - All trades logged to CSV
   - Signals displayed in real-time
   - Connection status monitoring

### File Structure
```
projects/fututradingbot/
├── src/
│   ├── realtime_bridge.py      # NEW: Real-time data bridge
│   ├── dashboard/
│   │   └── app.py              # MODIFIED: Connects to bridge
│   └── api/
│       └── futu_client.py      # Futu API client
├── templates/
│   └── dashboard.html          # MODIFIED: Shows prices + signals
├── start_dashboard.bat         # NEW: Startup script
└── logs/                       # Trading logs
```

### How to Start

Run `start_dashboard.bat` to start both services:
1. Realtime Bridge (port 8765)
2. Dashboard Server (port 8080)

Then open http://127.0.0.1:8080 and enter password: `futu2024`

### Notes
- Dashboard connects to bridge via WebSocket at ws://127.0.0.1:8765
- Bridge connects to Futu OpenD at 127.0.0.1:11111
- All prices are real-time from Futu API
- Signals are calculated using 20-period z-score
