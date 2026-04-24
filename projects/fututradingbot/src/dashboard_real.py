"""
Real-time Simulation Dashboard - 實時模擬交易Dashboard

連接至 simulation_bridge.py 提供真實模擬交易數據
"""

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import asyncio
import websockets
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Futu Trading - Real Simulation", version="2.0.0")

# Static files
static_path = Path(__file__).parent.parent / "static"
templates_path = Path(__file__).parent.parent / "templates"
static_path.mkdir(exist_ok=True)
templates_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Bridge connection
BRIDGE_URI = "ws://127.0.0.1:8765"


@app.get("/")
async def dashboard():
    """Main dashboard page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Futu Trading - Real Simulation</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
            .header { text-align: center; margin-bottom: 30px; }
            .status { display: inline-block; padding: 10px 20px; border-radius: 5px; }
            .status.running { background: #28a745; }
            .status.stopped { background: #dc3545; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .card { background: #2d2d2d; padding: 20px; border-radius: 10px; }
            .card h3 { margin-top: 0; color: #17a2b8; }
            .metric { display: flex; justify-content: space-between; margin: 10px 0; }
            .value { font-weight: bold; color: #ffc107; }
            .positive { color: #28a745; }
            .negative { color: #dc3545; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
            th { color: #17a2b8; }
            .log { background: #1a1a1a; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Futu Trading - Real Simulation</h1>
            <div class="status running" id="status">RUNNING</div>
            <p>Last Update: <span id="last-update">-</span></p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>💰 Account Summary</h3>
                <div class="metric">
                    <span>Cash:</span>
                    <span class="value" id="cash">-</span>
                </div>
                <div class="metric">
                    <span>Equity:</span>
                    <span class="value" id="equity">-</span>
                </div>
                <div class="metric">
                    <span>Daily P&L:</span>
                    <span class="value" id="daily-pnl">-</span>
                </div>
                <div class="metric">
                    <span>Total Trades:</span>
                    <span class="value" id="trade-count">-</span>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 Positions</h3>
                <div id="positions">
                    <p>No active positions</p>
                </div>
            </div>
            
            <div class="card" style="grid-column: 1 / -1;">
                <h3>📈 Recent Trades</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Action</th>
                            <th>Quantity</th>
                            <th>Price</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody id="trades">
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket('ws://' + window.location.host + '/ws');
            
            ws.onopen = function() {
                console.log('Connected to dashboard');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = function() {
                document.getElementById('status').textContent = 'DISCONNECTED';
                document.getElementById('status').className = 'status stopped';
            };
            
            function updateDashboard(data) {
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                
                if (data.account) {
                    document.getElementById('cash').textContent = '$' + data.account.cash?.toFixed(2);
                    document.getElementById('equity').textContent = '$' + data.account.equity?.toFixed(2);
                    
                    const pnl = data.account.daily_pnl || 0;
                    const pnlEl = document.getElementById('daily-pnl');
                    pnlEl.textContent = (pnl >= 0 ? '+' : '') + '$' + pnl.toFixed(2);
                    pnlEl.className = 'value ' + (pnl >= 0 ? 'positive' : 'negative');
                }
                
                document.getElementById('trade-count').textContent = data.trade_count || 0;
                
                // Update positions
                const posDiv = document.getElementById('positions');
                if (data.positions && Object.keys(data.positions).length > 0) {
                    let posHtml = '<table><tr><th>Symbol</th><th>Qty</th><th>Avg Cost</th></tr>';
                    for (const [sym, pos] of Object.entries(data.positions)) {
                        posHtml += `<tr><td>${sym}</td><td>${pos.quantity}</td><td>$${pos.avg_cost?.toFixed(2)}</td></tr>`;
                    }
                    posHtml += '</table>';
                    posDiv.innerHTML = posHtml;
                } else {
                    posDiv.innerHTML = '<p>No active positions</p>';
                }
                
                // Update trades
                const tradesBody = document.getElementById('trades');
                if (data.trades && data.trades.length > 0) {
                    tradesBody.innerHTML = data.trades.map(t => `
                        <tr>
                            <td>${new Date(t.timestamp).toLocaleTimeString()}</td>
                            <td>${t.symbol}</td>
                            <td class="${t.action === 'BUY' ? 'positive' : 'negative'}">${t.action}</td>
                            <td>${t.quantity}</td>
                            <td>$${t.price?.toFixed(2)}</td>
                            <td>${t.reason || '-'}</td>
                        </tr>
                    `).join('');
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection to bridge"""
    await websocket.accept()
    
    try:
        # Connect to bridge
        async with websockets.connect(BRIDGE_URI) as bridge_ws:
            while True:
                # Forward data from bridge to client
                data = await bridge_ws.recv()
                await websocket.send_text(data)
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8081)
