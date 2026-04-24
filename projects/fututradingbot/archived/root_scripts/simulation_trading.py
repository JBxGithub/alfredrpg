"""
FutuTradingBot Simulation Trading Script
模擬交易腳本 - TQQQ/SQQQ 配對交易 (含模擬數據模式)

當無法獲取實時行情時，使用模擬數據進行策略驗證
"""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

from src.api.futu_client import (
    FutuAPIClient, FutuQuoteClient, FutuTradeClient,
    Market, SubType, TrdEnv, TrdSide, OrderType
)
from src.strategies.pairs_trading import PairsTradingStrategy
from src.analysis.market_regime import MarketRegimeDetector, MarketRegime
from src.utils.logger import get_logger, logger

# Configuration
OPEND_HOST = "127.0.0.1"
OPEND_PORT = 11111
TQQQ_CODE = "US.TQQQ"
SQQQ_CODE = "US.SQQQ"

# Setup logger
logger = get_logger(__name__)


class MockDataGenerator:
    """模擬數據生成器 (當無法獲取實時行情時使用)"""
    
    @staticmethod
    def generate_tqqq_sqqq_data(days=100):
        """生成 TQQQ 和 SQQQ 的模擬歷史數據"""
        
        # 基礎價格 (基於近期大致價格範圍)
        base_tqqq = 38.0
        base_sqqq = 28.0
        
        # 生成日期序列
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=days, freq='D')
        
        # 生成相關的隨機走勢 (TQQQ 和 SQQQ 應該呈現負相關)
        np.random.seed(42)  # 可重現性
        
        # 市場基礎走勢 (模擬 NASDAQ)
        market_returns = np.random.normal(0.0005, 0.015, days)
        
        # TQQQ: 3x 槓桿做多 (波動放大)
        tqqq_returns = market_returns * 3 + np.random.normal(0, 0.005, days)
        tqqq_prices = base_tqqq * np.exp(np.cumsum(tqqq_returns))
        
        # SQQQ: 3x 槓桿做空 (與 TQQQ 負相關)
        sqqq_returns = -market_returns * 3 + np.random.normal(0, 0.005, days)
        sqqq_prices = base_sqqq * np.exp(np.cumsum(sqqq_returns))
        
        # 生成 OHLC 數據
        tqqq_data = []
        sqqq_data = []
        
        for i, date in enumerate(dates):
            # TQQQ
            close_tqqq = tqqq_prices[i]
            high_tqqq = close_tqqq * (1 + abs(np.random.normal(0, 0.01)))
            low_tqqq = close_tqqq * (1 - abs(np.random.normal(0, 0.01)))
            open_tqqq = tqqq_prices[i-1] if i > 0 else close_tqqq * (1 + np.random.normal(0, 0.005))
            
            tqqq_data.append({
                'time_key': date.strftime('%Y-%m-%d'),
                'open': open_tqqq,
                'high': high_tqqq,
                'low': low_tqqq,
                'close': close_tqqq,
                'volume': int(np.random.uniform(50000000, 150000000))
            })
            
            # SQQQ
            close_sqqq = sqqq_prices[i]
            high_sqqq = close_sqqq * (1 + abs(np.random.normal(0, 0.01)))
            low_sqqq = close_sqqq * (1 - abs(np.random.normal(0, 0.01)))
            open_sqqq = sqqq_prices[i-1] if i > 0 else close_sqqq * (1 + np.random.normal(0, 0.005))
            
            sqqq_data.append({
                'time_key': date.strftime('%Y-%m-%d'),
                'open': open_sqqq,
                'high': high_sqqq,
                'low': low_sqqq,
                'close': close_sqqq,
                'volume': int(np.random.uniform(30000000, 80000000))
            })
        
        df_tqqq = pd.DataFrame(tqqq_data)
        df_sqqq = pd.DataFrame(sqqq_data)
        
        return df_tqqq, df_sqqq


class SimulationTrader:
    """模擬交易執行器"""
    
    def __init__(self, use_mock_data=False):
        self.use_mock_data = use_mock_data
        self.api_client = FutuAPIClient(OPEND_HOST, OPEND_PORT)
        self.quote_client = None
        self.trade_client = None
        self.pairs_strategy = PairsTradingStrategy(config={
            'lookback_period': 60,
            'entry_zscore': 2.0,
            'exit_zscore': 0.5,
            'stop_loss_zscore': 3.5,
            'position_pct': 0.015,
            'min_correlation': 0.7,
            'hedge_ratio_window': 20
        })
        self.regime_detector = MarketRegimeDetector(lookback_period=20)
        
        # Data storage
        self.tqqq_data = pd.DataFrame()
        self.sqqq_data = pd.DataFrame()
        self.account_info = None
        self.positions = []
        self.trading_signals = []
        
        # Results
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'connection_status': False,
            'data_source': 'live' if not use_mock_data else 'mock',
            'account_balance': None,
            'market_regime': None,
            'tqqq_price': None,
            'sqqq_price': None,
            'pair_analysis': None,
            'trading_signals': [],
            'errors': []
        }
    
    def connect(self):
        """連接到 Futu OpenD"""
        logger.info("=" * 60)
        logger.info("Connecting to Futu OpenD...")
        logger.info(f"Host: {OPEND_HOST}:{OPEND_PORT}")
        
        try:
            # Connect quote client
            self.quote_client = FutuQuoteClient(OPEND_HOST, OPEND_PORT)
            if not self.quote_client.connect():
                error_msg = "Failed to connect to quote client"
                logger.error(error_msg)
                self.results['errors'].append(error_msg)
                return False
            
            # Connect trade client for US market
            self.trade_client = FutuTradeClient(OPEND_HOST, OPEND_PORT, Market.US)
            if not self.trade_client.connect():
                error_msg = "Failed to connect to trade client"
                logger.warning(error_msg)
                # Continue anyway for quote-only simulation
            
            self.results['connection_status'] = True
            logger.info("✓ Successfully connected to Futu OpenD")
            return True
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return False
    
    def try_subscribe_quotes(self):
        """嘗試訂閱行情，如果失敗則使用模擬數據"""
        logger.info("=" * 60)
        logger.info("Subscribing to TQQQ and SQQQ quotes...")
        
        try:
            ret_code, ret_data = self.quote_client.subscribe(
                code_list=[TQQQ_CODE, SQQQ_CODE],
                sub_types=[SubType.QUOTE, SubType.K_DAY, SubType.TICKER]
            )
            
            if ret_code == 0:
                logger.info("✓ Successfully subscribed to quotes")
                return True
            else:
                error_msg = f"Subscription failed: {ret_data}"
                logger.warning(error_msg)
                self.results['errors'].append(error_msg)
                logger.info("Switching to mock data mode...")
                self.use_mock_data = True
                self.results['data_source'] = 'mock'
                return False
                
        except Exception as e:
            error_msg = f"Subscription error: {str(e)}"
            logger.warning(error_msg)
            self.results['errors'].append(error_msg)
            logger.info("Switching to mock data mode...")
            self.use_mock_data = True
            self.results['data_source'] = 'mock'
            return False
    
    def get_account_balance(self):
        """獲取模擬賬戶資金"""
        logger.info("=" * 60)
        logger.info("Checking simulated account balance...")
        
        try:
            if self.trade_client:
                ret_code, ret_data = self.trade_client.accinfo_query(trd_env=TrdEnv.SIMULATE)
                
                if ret_code == 0:
                    self.account_info = ret_data
                    logger.info(f"✓ Account info retrieved")
                    
                    # Handle different return types
                    total_assets = ret_data.get('total_assets', 0)
                    cash = ret_data.get('cash', 0)
                    market_val = ret_data.get('market_val', 0)
                    
                    if isinstance(total_assets, pd.Series):
                        total_assets = float(total_assets.iloc[0]) if len(total_assets) > 0 else 0
                    if isinstance(cash, pd.Series):
                        cash = float(cash.iloc[0]) if len(cash) > 0 else 0
                    if isinstance(market_val, pd.Series):
                        market_val = float(market_val.iloc[0]) if len(market_val) > 0 else 0
                    
                    logger.info(f"  Total Assets: {total_assets}")
                    logger.info(f"  Cash: {cash}")
                    logger.info(f"  Market Value: {market_val}")
                    
                    self.results['account_balance'] = {
                        'total_assets': total_assets,
                        'cash': cash,
                        'market_value': market_val
                    }
                    return True
                else:
                    error_msg = f"Account query failed: {ret_data}"
                    logger.warning(error_msg)
            
            # Default simulation balance
            logger.info("Using default simulation balance")
            self.results['account_balance'] = {
                'total_assets': 1000000.0,
                'cash': 1000000.0,
                'market_value': 0.0,
                'note': 'Default simulation balance'
            }
            return True
                
        except Exception as e:
            error_msg = f"Account balance error: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            # Use default balance
            self.results['account_balance'] = {
                'total_assets': 1000000.0,
                'cash': 1000000.0,
                'market_value': 0.0,
                'note': 'Default simulation balance (error fallback)'
            }
            return True
    
    def get_market_data(self):
        """獲取市場數據 (實時或模擬)"""
        if self.use_mock_data:
            return self._get_mock_data()
        else:
            return self._get_live_data()
    
    def _get_live_data(self):
        """獲取實時市場數據"""
        logger.info("=" * 60)
        logger.info("Fetching live market data...")
        
        try:
            import futu as ft
            
            # Get TQQQ historical data
            ret_code1, tqqq_kline = self.quote_client.get_cur_kline(
                TQQQ_CODE, num=100, ktype=ft.KLType.K_DAY
            )
            
            # Get SQQQ historical data
            ret_code2, sqqq_kline = self.quote_client.get_cur_kline(
                SQQQ_CODE, num=100, ktype=ft.KLType.K_DAY
            )
            
            if ret_code1 == 0 and ret_code2 == 0:
                logger.info("✓ Live historical data retrieved")
                
                if isinstance(tqqq_kline, pd.DataFrame):
                    self.tqqq_data = tqqq_kline
                    logger.info(f"  TQQQ: {len(tqqq_kline)} days of data")
                
                if isinstance(sqqq_kline, pd.DataFrame):
                    self.sqqq_data = sqqq_kline
                    logger.info(f"  SQQQ: {len(sqqq_kline)} days of data")
                
                # Get current prices
                ret_code, snapshot = self.quote_client.get_market_snapshot([TQQQ_CODE, SQQQ_CODE])
                if ret_code == 0 and isinstance(snapshot, pd.DataFrame):
                    for _, row in snapshot.iterrows():
                        code = row.get('code', '')
                        last_price = row.get('last_price', 0)
                        
                        price_info = {
                            'last_price': float(last_price) if pd.notna(last_price) else None,
                            'open': float(row.get('open_price', 0)) if pd.notna(row.get('open_price')) else None,
                            'high': float(row.get('high_price', 0)) if pd.notna(row.get('high_price')) else None,
                            'low': float(row.get('low_price', 0)) if pd.notna(row.get('low_price')) else None,
                            'volume': int(row.get('volume', 0)) if pd.notna(row.get('volume')) else None
                        }
                        
                        if TQQQ_CODE in code:
                            self.results['tqqq_price'] = price_info
                        elif SQQQ_CODE in code:
                            self.results['sqqq_price'] = price_info
                
                return True
            else:
                error_msg = f"Live data failed: TQQQ={ret_code1}, SQQQ={ret_code2}"
                logger.warning(error_msg)
                self.results['errors'].append(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Live data error: {str(e)}"
            logger.warning(error_msg)
            self.results['errors'].append(error_msg)
            return False
    
    def _get_mock_data(self):
        """獲取模擬市場數據"""
        logger.info("=" * 60)
        logger.info("Generating mock market data...")
        
        try:
            df_tqqq, df_sqqq = MockDataGenerator.generate_tqqq_sqqq_data(days=100)
            
            self.tqqq_data = df_tqqq
            self.sqqq_data = df_sqqq
            
            logger.info(f"✓ Mock data generated")
            logger.info(f"  TQQQ: {len(df_tqqq)} days of data")
            logger.info(f"  SQQQ: {len(df_sqqq)} days of data")
            
            # Set current prices from mock data
            latest_tqqq = df_tqqq.iloc[-1]
            latest_sqqq = df_sqqq.iloc[-1]
            
            self.results['tqqq_price'] = {
                'last_price': round(latest_tqqq['close'], 2),
                'open': round(latest_tqqq['open'], 2),
                'high': round(latest_tqqq['high'], 2),
                'low': round(latest_tqqq['low'], 2),
                'volume': int(latest_tqqq['volume']),
                'note': 'Mock data'
            }
            
            self.results['sqqq_price'] = {
                'last_price': round(latest_sqqq['close'], 2),
                'open': round(latest_sqqq['open'], 2),
                'high': round(latest_sqqq['high'], 2),
                'low': round(latest_sqqq['low'], 2),
                'volume': int(latest_sqqq['volume']),
                'note': 'Mock data'
            }
            
            return True
            
        except Exception as e:
            error_msg = f"Mock data error: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return False
    
    def analyze_market_regime(self):
        """分析市場狀態"""
        logger.info("=" * 60)
        logger.info("Analyzing market regime...")
        
        try:
            if len(self.tqqq_data) < 20:
                logger.warning("Insufficient data for regime detection")
                self.results['market_regime'] = {
                    'regime': 'unknown',
                    'confidence': 0.0,
                    'note': 'Insufficient data'
                }
                return False
            
            # Use TQQQ as market proxy (leveraged NASDAQ)
            regime_state = self.regime_detector.detect(self.tqqq_data)
            
            self.results['market_regime'] = {
                'regime': regime_state.regime.value,
                'volatility_regime': regime_state.volatility_regime.value,
                'confidence': round(regime_state.confidence, 4),
                'duration': regime_state.duration,
                'features': {
                    'returns': round(regime_state.features.returns, 6) if regime_state.features.returns else 0,
                    'volatility': round(regime_state.features.volatility, 4) if regime_state.features.volatility else 0,
                    'trend_strength': round(regime_state.features.trend_strength, 2) if regime_state.features.trend_strength else 0,
                    'adx': round(regime_state.features.adx, 2) if regime_state.features.adx else 0,
                    'sentiment_score': round(regime_state.features.sentiment_score, 2) if regime_state.features.sentiment_score else 0
                }
            }
            
            logger.info(f"✓ Market regime detected: {regime_state.regime.value}")
            logger.info(f"  Confidence: {regime_state.confidence:.2%}")
            logger.info(f"  Volatility: {regime_state.volatility_regime.value}")
            
            return True
            
        except Exception as e:
            error_msg = f"Market regime analysis error: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            self.results['market_regime'] = {
                'regime': 'error',
                'confidence': 0.0,
                'error': str(e)
            }
            return False
    
    def generate_trading_signals(self):
        """生成交易信號"""
        logger.info("=" * 60)
        logger.info("Generating trading signals...")
        
        try:
            # Register the pair
            self.pairs_strategy.register_pair('TQQQ_SQQQ', TQQQ_CODE, SQQQ_CODE)
            
            # Prepare data for strategy
            if len(self.tqqq_data) >= 60 and len(self.sqqq_data) >= 60:
                
                # Update price data in strategy
                self.pairs_strategy.price_data[TQQQ_CODE] = self.tqqq_data
                self.pairs_strategy.price_data[SQQQ_CODE] = self.sqqq_data
                
                # Get pair analysis
                analysis = self.pairs_strategy.get_pair_analysis('TQQQ_SQQQ')
                
                if analysis:
                    logger.info(f"✓ Pair analysis completed")
                    logger.info(f"  Z-Score: {analysis.get('zscore')}")
                    logger.info(f"  Correlation: {analysis.get('correlation')}")
                    logger.info(f"  Hedge Ratio: {analysis.get('hedge_ratio')}")
                    
                    signal_info = {
                        'pair_id': 'TQQQ_SQQQ',
                        'asset1': TQQQ_CODE,
                        'asset2': SQQQ_CODE,
                        'zscore': round(analysis.get('zscore', 0), 4) if analysis.get('zscore') is not None else None,
                        'correlation': round(analysis.get('correlation', 0), 4) if analysis.get('correlation') is not None else None,
                        'hedge_ratio': round(analysis.get('hedge_ratio', 0), 4) if analysis.get('hedge_ratio') is not None else None,
                        'has_position': analysis.get('has_position', False),
                        'signal': None,
                        'recommendation': None,
                        'strategy_params': {
                            'entry_zscore': self.pairs_strategy.entry_zscore,
                            'exit_zscore': self.pairs_strategy.exit_zscore,
                            'stop_loss_zscore': self.pairs_strategy.stop_loss_zscore,
                            'min_correlation': self.pairs_strategy.min_correlation
                        }
                    }
                    
                    # Generate signal based on z-score
                    zscore = analysis.get('zscore')
                    correlation = analysis.get('correlation', 0)
                    
                    if correlation < self.pairs_strategy.min_correlation:
                        signal_info['signal'] = 'NO_TRADE'
                        signal_info['recommendation'] = f'Correlation too low ({correlation:.2f}). Minimum required: {self.pairs_strategy.min_correlation}'
                    elif zscore is not None:
                        if zscore > self.pairs_strategy.entry_zscore:
                            signal_info['signal'] = 'LONG_TQQQ_SHORT_SQQQ'
                            signal_info['recommendation'] = f'TQQQ is relatively undervalued vs SQQQ (Z={zscore:.2f}). Consider buying TQQQ and hedging with SQQQ short.'
                            signal_info['strength'] = 'STRONG' if zscore > 2.5 else 'MODERATE'
                        elif zscore < -self.pairs_strategy.entry_zscore:
                            signal_info['signal'] = 'LONG_SQQQ_SHORT_TQQQ'
                            signal_info['recommendation'] = f'SQQQ is relatively undervalued vs TQQQ (Z={zscore:.2f}). Consider buying SQQQ and hedging with TQQQ short.'
                            signal_info['strength'] = 'STRONG' if zscore < -2.5 else 'MODERATE'
                        elif abs(zscore) < self.pairs_strategy.exit_zscore:
                            signal_info['signal'] = 'HOLD'
                            signal_info['recommendation'] = f'Spread is near mean (Z={zscore:.2f}). No trading signal.'
                            signal_info['strength'] = 'NONE'
                        else:
                            signal_info['signal'] = 'WAIT'
                            signal_info['recommendation'] = f'Z-score ({zscore:.2f}) not at extreme levels. Wait for better entry.'
                            signal_info['strength'] = 'WEAK'
                    
                    self.results['trading_signals'].append(signal_info)
                    self.results['pair_analysis'] = {
                        'zscore': signal_info['zscore'],
                        'correlation': signal_info['correlation'],
                        'hedge_ratio': signal_info['hedge_ratio']
                    }
                    
                    logger.info(f"  Signal: {signal_info['signal']}")
                    logger.info(f"  Recommendation: {signal_info['recommendation']}")
                    
                    return True
                else:
                    logger.warning("Could not generate pair analysis")
                    return False
            else:
                logger.warning("Insufficient historical data for signal generation")
                return False
                
        except Exception as e:
            error_msg = f"Signal generation error: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            self.results['errors'].append(error_msg)
            return False
    
    def run(self):
        """運行完整模擬流程"""
        logger.info("\n" + "=" * 60)
        logger.info("FutuTradingBot Simulation Trading Started")
        logger.info("=" * 60)
        logger.info(f"Time: {datetime.now().isoformat()}")
        logger.info(f"Symbols: {TQQQ_CODE}, {SQQQ_CODE}")
        logger.info("=" * 60)
        
        # Step 1: Connect to OpenD
        if not self.connect():
            logger.error("Failed to connect to OpenD. Switching to offline mode.")
            self.use_mock_data = True
            self.results['data_source'] = 'mock'
            self.results['connection_status'] = False
        
        # Step 2: Try to subscribe to quotes (may fail due to permissions)
        if self.results['connection_status']:
            self.try_subscribe_quotes()
        
        # Step 3: Get account balance
        self.get_account_balance()
        
        # Step 4: Get market data (live or mock)
        self.get_market_data()
        
        # Step 5: Analyze market regime
        self.analyze_market_regime()
        
        # Step 6: Generate trading signals
        self.generate_trading_signals()
        
        # Cleanup
        self.cleanup()
        
        # Log summary
        self.log_summary()
        
        return self.results
    
    def cleanup(self):
        """清理資源"""
        logger.info("=" * 60)
        logger.info("Cleaning up resources...")
        
        if self.quote_client:
            self.quote_client.close()
        
        if self.trade_client:
            self.trade_client.close()
        
        logger.info("✓ Cleanup completed")
    
    def log_summary(self):
        """記錄摘要"""
        logger.info("\n" + "=" * 60)
        logger.info("SIMULATION TRADING SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"Connection Status: {'✓ Connected' if self.results['connection_status'] else '✗ Not Connected'}")
        logger.info(f"Data Source: {self.results['data_source'].upper()}")
        
        if self.results['account_balance']:
            balance = self.results['account_balance']
            logger.info(f"Account Balance:")
            logger.info(f"  Total Assets: ${balance.get('total_assets', 'N/A'):,.2f}" if isinstance(balance.get('total_assets'), (int, float)) else f"  Total Assets: {balance.get('total_assets', 'N/A')}")
            logger.info(f"  Cash: ${balance.get('cash', 'N/A'):,.2f}" if isinstance(balance.get('cash'), (int, float)) else f"  Cash: {balance.get('cash', 'N/A')}")
        
        if self.results['market_regime']:
            regime = self.results['market_regime']
            logger.info(f"Market Regime:")
            logger.info(f"  Regime: {regime.get('regime', 'N/A').upper()}")
            logger.info(f"  Confidence: {regime.get('confidence', 'N/A')}")
            logger.info(f"  Volatility: {regime.get('volatility_regime', 'N/A').upper()}")
        
        if self.results['tqqq_price']:
            price = self.results['tqqq_price']
            note = f" ({price.get('note', '')})" if price.get('note') else ""
            logger.info(f"TQQQ Price: ${price.get('last_price', 'N/A')}{note}")
        
        if self.results['sqqq_price']:
            price = self.results['sqqq_price']
            note = f" ({price.get('note', '')})" if price.get('note') else ""
            logger.info(f"SQQQ Price: ${price.get('last_price', 'N/A')}{note}")
        
        if self.results['pair_analysis']:
            analysis = self.results['pair_analysis']
            logger.info(f"Pair Analysis:")
            logger.info(f"  Z-Score: {analysis.get('zscore', 'N/A')}")
            logger.info(f"  Correlation: {analysis.get('correlation', 'N/A')}")
            logger.info(f"  Hedge Ratio: {analysis.get('hedge_ratio', 'N/A')}")
        
        if self.results['trading_signals']:
            for sig in self.results['trading_signals']:
                logger.info(f"Trading Signal: {sig.get('signal', 'N/A')}")
                if sig.get('strength'):
                    logger.info(f"  Strength: {sig.get('strength')}")
                logger.info(f"  Recommendation: {sig.get('recommendation', 'N/A')}")
        
        if self.results['errors']:
            logger.warning(f"Errors/Warnings ({len(self.results['errors'])}):")
            for err in self.results['errors']:
                logger.warning(f"  - {err}")
        
        logger.info("=" * 60)


def main():
    """主函數"""
    # Check if mock data mode is requested
    use_mock = '--mock' in sys.argv or '-m' in sys.argv
    
    trader = SimulationTrader(use_mock_data=use_mock)
    results = trader.run()
    
    # Save results to file
    output_dir = Path(project_root) / "logs"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\nResults saved to: {output_file}")
    
    # Print final results
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    results = main()
    sys.exit(0 if results['account_balance'] else 1)
