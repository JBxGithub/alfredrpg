import yfinance as yf
import pandas as pd
import numpy as np
import talib
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Database setup
DATABASE_URL = "postgresql://username:password@localhost:5432/your_database"  # Replace with actual DB URL
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class ReferenceScore(Base):
    __tablename__ = 'reference_scores'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    score = Column(Float)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# NQ100 top 50 constituents (example list, update with actual top 50)
NQ100_TOP50 = [
    'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA', 'NVDA', 'META', 'NFLX', 'BABA', 'ORCL',
    'CRM', 'AMD', 'INTC', 'CSCO', 'CMCSA', 'ADBE', 'PYPL', 'QCOM', 'TXN', 'AVGO',
    'MU', 'LRCX', 'AMAT', 'KLAC', 'ISRG', 'IDXX', 'ILMN', 'DXCM', 'ALGN', 'SGEN',
    'REGN', 'VRTX', 'BIIB', 'GILD', 'AMGN', 'MRNA', 'PFE', 'JNJ', 'ABT', 'TMO',
    'DHR', 'WAT', 'A', 'PKI', 'BIO', 'BRKR', 'MTD', 'IQV', 'EW', 'LH'
]  # This is a placeholder; fetch actual list if needed

def fetch_stock_data(ticker, period="1mo"):
    """Fetch historical stock data."""
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

def calculate_strength_ratio(stocks_data):
    """Calculate strength ratio: % of stocks where close > open in recent period."""
    strong_count = 0
    total = len(stocks_data)
    for data in stocks_data:
        if not data.empty:
            recent = data.iloc[-1]
            if recent['Close'] > recent['Open']:
                strong_count += 1
    ratio = strong_count / total if total > 0 else 0
    return ratio

def calculate_technical_indicators(data):
    """Calculate RSI, MACD, Bollinger Bands and return a score."""
    if data.empty or len(data) < 30:
        return 0  # Insufficient data

    close = data['Close'].values

    # RSI (14-period)
    rsi = talib.RSI(close, timeperiod=14)
    rsi_score = 1 if rsi[-1] > 70 else (0.5 if rsi[-1] > 30 else 0)  # Overbought: 1, Neutral: 0.5, Oversold: 0

    # MACD
    macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    macd_score = 1 if macdhist[-1] > 0 else 0  # Bullish if histogram positive

    # Bollinger Bands
    upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    bb_score = 1 if close[-1] < upper[-1] and close[-1] > lower[-1] else 0  # Within bands: 1

    # Average score
    tech_score = (rsi_score + macd_score + bb_score) / 3
    return tech_score

def calculate_volume_price_indicators(data):
    """Calculate volume and price change indicators."""
    if data.empty or len(data) < 2:
        return 0

    # Volume change: recent volume vs average
    volume = data['Volume'].values
    avg_volume = np.mean(volume[:-1])  # Exclude latest
    vol_change = (volume[-1] - avg_volume) / avg_volume if avg_volume > 0 else 0
    vol_score = min(max(vol_change, -1), 1)  # Normalize to [-1, 1], then to [0,1]
    vol_score = (vol_score + 1) / 2

    # Price change: recent close vs previous close
    price_change = (data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]
    price_score = min(max(price_change, -0.1), 0.1)  # Cap at ±10%, normalize to [0,1]
    price_score = (price_score + 0.1) / 0.2

    # Average
    flow_score = (vol_score + price_score) / 2
    return flow_score

def calculate_reference_score():
    """Main function to calculate and store reference score."""
    stocks_data = []
    tech_scores = []
    flow_scores = []

    for ticker in NQ100_TOP50[:50]:  # Ensure top 50
        data = fetch_stock_data(ticker)
        stocks_data.append(data)
        if not data.empty:
            tech_scores.append(calculate_technical_indicators(data))
            flow_scores.append(calculate_volume_price_indicators(data))

    # Strength ratio (30%)
    strength_ratio = calculate_strength_ratio(stocks_data)
    strength_weight = 0.3 * strength_ratio

    # Technical indicators (40%) - average across stocks
    tech_avg = np.mean(tech_scores) if tech_scores else 0
    tech_weight = 0.4 * tech_avg

    # Volume/Price indicators (30%) - average across stocks
    flow_avg = np.mean(flow_scores) if flow_scores else 0
    flow_weight = 0.3 * flow_avg

    # Total score
    total_score = strength_weight + tech_weight + flow_weight

    # Store in DB
    ref_score = ReferenceScore(score=total_score)
    session.add(ref_score)
    session.commit()

    return total_score

if __name__ == "__main__":
    score = calculate_reference_score()
    print(f"Reference Score calculated and stored: {score}")