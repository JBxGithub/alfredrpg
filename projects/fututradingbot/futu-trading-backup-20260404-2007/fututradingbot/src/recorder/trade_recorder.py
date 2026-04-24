import csv
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

class TradeRecorder:
    """
    Records trades to daily CSV files.
    Filename format: trades_YYYY-MM-DD.csv
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Default to project root / data / trades
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "trades"
        else:
            self.data_dir = Path(data_dir)
        
        # Ensure directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # CSV columns
        self.columns = ["time", "symbol", "action", "quantity", "price", "fee", "pnl"]
    
    def _get_today_filename(self) -> Path:
        """Get today's CSV filename"""
        today = date.today().strftime("%Y-%m-%d")
        return self.data_dir / f"trades_{today}.csv"
    
    def _ensure_file_exists(self, filepath: Path):
        """Create CSV file with headers if it doesn't exist"""
        if not filepath.exists():
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writeheader()
    
    def record_trade(self, trade_data: Dict) -> bool:
        """
        Record a single trade to today's CSV file.
        
        Args:
            trade_data: Dictionary with keys: time, symbol, action, quantity, price, fee, pnl
        
        Returns:
            bool: True if successful
        """
        try:
            filepath = self._get_today_filename()
            self._ensure_file_exists(filepath)
            
            # Ensure all required fields exist
            row = {col: trade_data.get(col, "") for col in self.columns}
            
            # Add timestamp if not provided
            if not row["time"]:
                row["time"] = datetime.now().strftime("%H:%M:%S")
            
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"Error recording trade: {e}")
            return False
    
    def get_today_trades(self) -> List[Dict]:
        """Get all trades from today"""
        filepath = self._get_today_filename()
        
        if not filepath.exists():
            return []
        
        trades = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(dict(row))
        
        return trades
    
    def get_trades_by_date(self, trade_date: date) -> List[Dict]:
        """Get trades for a specific date"""
        filename = self.data_dir / f"trades_{trade_date.strftime('%Y-%m-%d')}.csv"
        
        if not filename.exists():
            return []
        
        trades = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(dict(row))
        
        return trades
    
    def get_trade_summary(self, trade_date: date = None) -> Dict:
        """
        Get summary statistics for trades on a specific date.
        
        Returns:
            Dict with total_trades, total_buy, total_sell, total_pnl, total_fees
        """
        if trade_date is None:
            trade_date = date.today()
        
        trades = self.get_trades_by_date(trade_date)
        
        summary = {
            "date": trade_date.strftime("%Y-%m-%d"),
            "total_trades": len(trades),
            "total_buy": 0,
            "total_sell": 0,
            "total_pnl": 0.0,
            "total_fees": 0.0
        }
        
        for trade in trades:
            action = trade.get("action", "").upper()
            if action == "BUY":
                summary["total_buy"] += 1
            elif action == "SELL":
                summary["total_sell"] += 1
            
            try:
                summary["total_pnl"] += float(trade.get("pnl", 0) or 0)
                summary["total_fees"] += float(trade.get("fee", 0) or 0)
            except (ValueError, TypeError):
                pass
        
        summary["total_pnl"] = round(summary["total_pnl"], 2)
        summary["total_fees"] = round(summary["total_fees"], 2)
        
        return summary
    
    def list_available_dates(self) -> List[str]:
        """List all dates that have trade records"""
        dates = []
        for file in self.data_dir.glob("trades_*.csv"):
            # Extract date from filename
            date_str = file.stem.replace("trades_", "")
            dates.append(date_str)
        
        return sorted(dates, reverse=True)

# Singleton instance for easy import
_default_recorder = None

def get_recorder() -> TradeRecorder:
    """Get the default trade recorder instance"""
    global _default_recorder
    if _default_recorder is None:
        _default_recorder = TradeRecorder()
    return _default_recorder

if __name__ == "__main__":
    # Test the recorder
    recorder = TradeRecorder()
    
    # Record a test trade
    test_trade = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "symbol": "AAPL",
        "action": "BUY",
        "quantity": 100,
        "price": 150.00,
        "fee": 15.00,
        "pnl": 0.0
    }
    
    recorder.record_trade(test_trade)
    print(f"Recorded trade: {test_trade}")
    
    # Get today's trades
    trades = recorder.get_today_trades()
    print(f"Today's trades: {trades}")
    
    # Get summary
    summary = recorder.get_trade_summary()
    print(f"Trade summary: {summary}")
