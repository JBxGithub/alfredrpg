"""
FutuTradingBot Live Connection Test
Test connection to Futu OpenD and subscription for TQQQ/SQQQ
"""
import sys
sys.path.insert(0, 'src')

import time
import pandas as pd
from datetime import datetime

from src.api.futu_client import FutuAPIClient, Market, SubType
from src.analysis.market_regime import MarketRegimeDetector, MarketRegime
from src.utils.logger import logger

# Test configuration
OPEND_HOST = "127.0.0.1"
OPEND_PORT = 11111
TEST_SYMBOLS = ["US.TQQQ", "US.SQQQ"]  # Nasdaq leveraged ETFs

class LiveDataTest:
    def __init__(self):
        self.api_client = None
        self.subscription_status = {}
        self.realtime_quotes = {}
        self.market_data = {}
        
    def connect(self):
        """Connect to Futu OpenD"""
        print("=" * 60)
        print("🔌 Connecting to Futu OpenD...")
        print(f"   Host: {OPEND_HOST}:{OPEND_PORT}")
        print("=" * 60)
        
        self.api_client = FutuAPIClient(OPEND_HOST, OPEND_PORT)
        
        # Connect quote client
        if not self.api_client.connect_quote():
            print("❌ Failed to connect to quote service!")
            return False
        
        print("✅ Quote client connected successfully!")
        return True
    
    def subscribe_quotes(self):
        """Subscribe to TQQQ and SQQQ real-time quotes"""
        print("\n" + "=" * 60)
        print("📊 Subscribing to real-time quotes...")
        print(f"   Symbols: {', '.join(TEST_SYMBOLS)}")
        print("=" * 60)
        
        quote_client = self.api_client.get_quote_client()
        if not quote_client:
            print("❌ Quote client not available!")
            return False
        
        # Subscribe to quote data (including kline for analysis)
        import futu as ft
        sub_types = [SubType.QUOTE, SubType.TICKER, SubType.K_5M]
        ret_code, ret_data = quote_client.subscribe(TEST_SYMBOLS, sub_types)
        
        if ret_code == 0:
            print("✅ Subscription successful!")
            for symbol in TEST_SYMBOLS:
                self.subscription_status[symbol] = "SUCCESS"
            return True
        else:
            print(f"❌ Subscription failed!")
            print(f"   Error code: {ret_code}")
            print(f"   Error data: {ret_data}")
            
            # Check for permission error (无权限)
            error_str = str(ret_data)
            if "无权限" in error_str or "permission" in error_str.lower():
                print("⚠️  PERMISSION ERROR: Nasdaq Basic/TotalView subscription required!")
                for symbol in TEST_SYMBOLS:
                    self.subscription_status[symbol] = "FAILED - NO PERMISSION"
            else:
                for symbol in TEST_SYMBOLS:
                    self.subscription_status[symbol] = f"FAILED - {ret_data}"
            return False
    
    def get_realtime_prices(self):
        """Get real-time prices for TQQQ and SQQQ"""
        print("\n" + "=" * 60)
        print("💰 Fetching real-time prices...")
        print("=" * 60)
        
        quote_client = self.api_client.get_quote_client()
        if not quote_client:
            print("❌ Quote client not available!")
            return False
        
        # Get stock quotes
        ret_code, ret_data = quote_client.get_stock_quote(TEST_SYMBOLS)
        
        if ret_code == 0:
            print("✅ Real-time prices retrieved!")
            print("\n📈 Price Data:")
            print("-" * 60)
            
            for symbol in TEST_SYMBOLS:
                try:
                    symbol_data = ret_data[ret_data['code'] == symbol]
                    if not symbol_data.empty:
                        price = symbol_data['last_price'].values[0]
                        open_price = symbol_data['open_price'].values[0]
                        high = symbol_data['high_price'].values[0]
                        low = symbol_data['low_price'].values[0]
                        volume = symbol_data['volume'].values[0]
                        change = ((price - open_price) / open_price * 100) if open_price > 0 else 0
                        
                        self.realtime_quotes[symbol] = {
                            'price': price,
                            'open': open_price,
                            'high': high,
                            'low': low,
                            'volume': volume,
                            'change_pct': change,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        print(f"\n   {symbol}:")
                        print(f"      Price: ${price:.2f}")
                        print(f"      Change: {change:+.2f}%")
                        print(f"      High: ${high:.2f} | Low: ${low:.2f}")
                        print(f"      Volume: {volume:,}")
                    else:
                        print(f"   {symbol}: No data available")
                        self.realtime_quotes[symbol] = None
                except Exception as e:
                    print(f"   {symbol}: Error retrieving data - {e}")
                    self.realtime_quotes[symbol] = None
            
            return True
        else:
            print(f"❌ Failed to get prices!")
            print(f"   Error: {ret_data}")
            return False
    
    def get_historical_data(self):
        """Get historical kline data for analysis"""
        print("\n" + "=" * 60)
        print("📉 Fetching historical data for analysis...")
        print("=" * 60)
        
        quote_client = self.api_client.get_quote_client()
        if not quote_client:
            return False
        
        import futu as ft
        
        for symbol in TEST_SYMBOLS:
            try:
                ret_code, ret_data = quote_client.get_cur_kline(symbol, num=60, ktype=ft.KLType.K_5M)
                if ret_code == 0:
                    self.market_data[symbol] = ret_data
                    print(f"✅ {symbol}: Retrieved {len(ret_data)} klines")
                else:
                    print(f"❌ {symbol}: Failed to get kline data - {ret_data}")
                    self.market_data[symbol] = None
            except Exception as e:
                print(f"❌ {symbol}: Error - {e}")
                self.market_data[symbol] = None
        
        return any(v is not None for v in self.market_data.values())
    
    def run_pair_trading_analysis(self):
        """Run pair trading analysis with live data"""
        print("\n" + "=" * 60)
        print("🔗 Running Pair Trading Analysis...")
        print("=" * 60)
        
        if not self.realtime_quotes or not all(self.realtime_quotes.values()):
            print("❌ No real-time price data available for analysis")
            return None
        
        tqqq = self.realtime_quotes.get("US.TQQQ")
        sqqq = self.realtime_quotes.get("US.SQQQ")
        
        if not tqqq or not sqqq:
            print("❌ Missing price data for one or both symbols")
            return None
        
        # Calculate pair metrics
        tqqq_price = tqqq['price']
        sqqq_price = sqqq['price']
        
        # Inverse relationship check (TQQQ should move opposite to SQQQ)
        tqqq_change = tqqq['change_pct']
        sqqq_change = sqqq['change_pct']
        
        # Calculate spread
        spread = tqqq_change - (-sqqq_change)  # TQQQ change minus inverse of SQQQ change
        
        print(f"\n📊 Pair Analysis:")
        print("-" * 60)
        print(f"   TQQQ Change: {tqqq_change:+.2f}%")
        print(f"   SQQQ Change: {sqqq_change:+.2f}%")
        print(f"   Spread (TQQQ - (-SQQQ)): {spread:+.2f}%")
        print(f"   Correlation Check: {'✅ Normal' if abs(spread) < 2 else '⚠️ Anomaly detected'}")
        
        # Generate trading signals
        signals = []
        
        if abs(spread) > 1.5:
            if spread > 0:
                signals.append("📉 SQQQ underperforming - Consider SQQQ LONG / TQQQ SHORT")
            else:
                signals.append("📈 TQQQ underperforming - Consider TQQQ LONG / SQQQ SHORT")
        
        if abs(tqqq_change) > 3 or abs(sqqq_change) > 3:
            signals.append("⚠️ High volatility detected - Reduce position size")
        
        if tqqq_change > 2 and sqqq_change > -2:
            signals.append("🚀 Tech rally - TQQQ momentum strong")
        elif tqqq_change < -2 and sqqq_change < 2:
            signals.append("🔻 Tech selloff - SQQQ momentum strong")
        
        if not signals:
            signals.append("⏸️ No clear signal - Hold positions")
        
        print(f"\n🎯 Trading Signals:")
        for signal in signals:
            print(f"   {signal}")
        
        return {
            'tqqq_change': tqqq_change,
            'sqqq_change': sqqq_change,
            'spread': spread,
            'signals': signals
        }
    
    def analyze_market_regime(self):
        """Analyze market regime using historical data"""
        print("\n" + "=" * 60)
        print("🌊 Market Regime Analysis...")
        print("=" * 60)
        
        if not self.market_data.get("US.TQQQ") is not None:
            print("❌ No historical data available for regime analysis")
            return None
        
        try:
            df = self.market_data["US.TQQQ"]
            
            # Ensure column names match expected format
            if 'close' not in df.columns:
                # Map common Futu API column names
                column_map = {
                    'close_price': 'close',
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'volume': 'volume'
                }
                df = df.rename(columns=column_map)
            
            detector = MarketRegimeDetector(lookback_period=20)
            state = detector.detect(df)
            
            regime_names = {
                MarketRegime.TRENDING_UP: "📈 TRENDING UP (上升趨勢)",
                MarketRegime.TRENDING_DOWN: "📉 TRENDING DOWN (下降趨勢)",
                MarketRegime.RANGING: "↔️ RANGING (震盪整理)",
                MarketRegime.HIGH_VOLATILITY: "⚡ HIGH VOLATILITY (高波動)",
                MarketRegime.UNKNOWN: "❓ UNKNOWN (未知)"
            }
            
            print(f"\n   Current Regime: {regime_names.get(state.regime, state.regime.value)}")
            print(f"   Confidence: {state.confidence:.1%}")
            print(f"   Volatility Regime: {state.volatility_regime.value}")
            print(f"   Duration: {state.duration} periods")
            
            if state.features:
                print(f"\n   Features:")
                print(f"      Trend Strength: {state.features.trend_strength:.1f}/100")
                print(f"      ADX: {state.features.adx:.2f}")
                print(f"      Volatility: {state.features.volatility:.2%}")
                print(f"      Fear/Greed Index: {state.features.fear_greed_index:.1f}")
            
            return state
            
        except Exception as e:
            print(f"❌ Error in regime analysis: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def close(self):
        """Close connections"""
        if self.api_client:
            print("\n🔌 Closing connections...")
            self.api_client.disconnect_all()
            print("✅ Connections closed")
    
    def run_full_test(self):
        """Run complete test suite"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'connection': False,
            'subscription': {},
            'prices': {},
            'market_regime': None,
            'pair_analysis': None
        }
        
        try:
            # Step 1: Connect
            results['connection'] = self.connect()
            if not results['connection']:
                return results
            
            # Step 2: Subscribe
            sub_success = self.subscribe_quotes()
            results['subscription'] = self.subscription_status
            
            if not sub_success:
                print("\n⚠️ Subscription failed - cannot proceed with live data tests")
                return results
            
            # Step 3: Get real-time prices
            self.get_realtime_prices()
            results['prices'] = self.realtime_quotes
            
            # Step 4: Get historical data
            self.get_historical_data()
            
            # Step 5: Market regime analysis
            results['market_regime'] = self.analyze_market_regime()
            
            # Step 6: Pair trading analysis
            results['pair_analysis'] = self.run_pair_trading_analysis()
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()
        
        return results
    
    def print_summary(self, results):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        print(f"\n⏰ Test Time: {results['timestamp']}")
        
        # Connection status
        conn_status = "✅ CONNECTED" if results['connection'] else "❌ FAILED"
        print(f"\n🔌 OpenD Connection: {conn_status}")
        
        # Subscription status
        print(f"\n📊 Subscription Status:")
        for symbol, status in results['subscription'].items():
            icon = "✅" if "SUCCESS" in status else "❌"
            print(f"   {icon} {symbol}: {status}")
        
        # Prices
        print(f"\n💰 Real-Time Prices:")
        for symbol, data in results['prices'].items():
            if data:
                print(f"   {symbol}: ${data['price']:.2f} ({data['change_pct']:+.2f}%)")
            else:
                print(f"   {symbol}: No data")
        
        # Market Regime
        regime = results.get('market_regime')
        if regime:
            print(f"\n🌊 Market Regime: {regime.regime.value} (confidence: {regime.confidence:.1%})")
        else:
            print(f"\n🌊 Market Regime: Analysis failed")
        
        # Trading Signals
        pair_analysis = results.get('pair_analysis')
        if pair_analysis:
            print(f"\n🎯 Trading Signals:")
            for signal in pair_analysis['signals']:
                print(f"   {signal}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n" + "🚀 " * 30)
    print("   FUTU TRADING BOT - LIVE CONNECTION TEST")
    print("   Testing Nasdaq Basic + TotalView Subscription")
    print("🚀 " * 30 + "\n")
    
    test = LiveDataTest()
    results = test.run_full_test()
    test.print_summary(results)
    
    # Exit with appropriate code
    all_subscribed = all("SUCCESS" in str(s) for s in results['subscription'].values())
    sys.exit(0 if all_subscribed else 1)
