"""
特徵工程模組 - Feature Engineering

技術指標特徵提取、K線形態特徵編碼、市場情緒特徵整合

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    StandardScaler = None
    MinMaxScaler = None

import warnings

from src.indicators.technical import TechnicalIndicators
from src.indicators.candlestick_patterns import CandlestickAnalyzer, PatternType
from src.analysis.market_sentiment import MarketSentimentAnalyzer
from src.utils.logger import logger

warnings.filterwarnings('ignore')


@dataclass
class FeatureConfig:
    """特徵配置"""
    include_technical: bool = True
    include_candlestick: bool = True
    include_sentiment: bool = True
    include_price_action: bool = True
    normalize: bool = True
    scaler_type: str = "standard"  # standard, minmax


class FeatureEngineer:
    """
    特徵工程類
    
    從原始價格數據中提取機器學習特徵
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
        self.candlestick_analyzer = CandlestickAnalyzer()
        self.sentiment_analyzer = MarketSentimentAnalyzer()
        self.scaler = None
        
        if self.config.normalize and SKLEARN_AVAILABLE:
            if self.config.scaler_type == "standard":
                self.scaler = StandardScaler()
            else:
                self.scaler = MinMaxScaler()
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取所有特徵
        
        Args:
            df: 原始價格數據
            
        Returns:
            DataFrame: 特徵數據
        """
        features_list = []
        
        if self.config.include_price_action:
            price_features = self._extract_price_features(df)
            features_list.append(price_features)
        
        if self.config.include_technical:
            technical_features = self._extract_technical_features(df)
            features_list.append(technical_features)
        
        if self.config.include_candlestick:
            candlestick_features = self._extract_candlestick_features(df)
            features_list.append(candlestick_features)
        
        if self.config.include_sentiment:
            sentiment_features = self._extract_sentiment_features(df)
            features_list.append(sentiment_features)
        
        # 合併所有特徵
        if features_list:
            all_features = pd.concat(features_list, axis=1)
        else:
            all_features = pd.DataFrame(index=df.index)
        
        # 移除無限值和NaN
        all_features = all_features.replace([np.inf, -np.inf], np.nan)
        all_features = all_features.ffill().bfill().fillna(0)
        
        return all_features
    
    def _extract_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取價格行為特徵"""
        features = pd.DataFrame(index=df.index)
        
        close = df['close']
        high = df['high']
        low = df['low']
        open_price = df['open']
        volume = df.get('volume', pd.Series(1, index=df.index))
        
        # 收益率特徵
        features['returns_1d'] = close.pct_change(1)
        features['returns_5d'] = close.pct_change(5)
        features['returns_10d'] = close.pct_change(10)
        features['returns_20d'] = close.pct_change(20)
        
        # 波動率特徵
        features['volatility_5d'] = features['returns_1d'].rolling(5).std()
        features['volatility_20d'] = features['returns_1d'].rolling(20).std()
        
        # 價格位置特徵
        features['price_position'] = (close - low.rolling(20).min()) / (high.rolling(20).max() - low.rolling(20).min())
        
        # 高低點特徵
        features['high_low_ratio'] = high / low
        features['close_open_ratio'] = close / open_price
        
        # 成交量特徵
        features['volume_ratio'] = volume / volume.rolling(20).mean()
        features['volume_change'] = volume.pct_change()
        
        # 價格趨勢特徵
        features['trend_5d'] = (close > close.shift(5)).astype(float)
        features['trend_10d'] = (close > close.shift(10)).astype(float)
        features['trend_20d'] = (close > close.shift(20)).astype(float)
        
        return features
    
    def _extract_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取技術指標特徵"""
        features = pd.DataFrame(index=df.index)
        
        ti = TechnicalIndicators(df)
        
        # MACD特徵
        macd = ti.calculate_macd()
        features['macd_dif'] = macd.dif
        features['macd_dea'] = macd.dea
        features['macd_histogram'] = macd.macd
        features['macd_signal'] = (macd.dif > macd.dea).astype(float)
        
        # RSI特徵
        rsi = ti.calculate_rsi()
        features['rsi_6'] = rsi.rsi_6
        features['rsi_12'] = rsi.rsi_12
        features['rsi_24'] = rsi.rsi_24
        features['rsi_oversold'] = (rsi.rsi_12 < 30).astype(float)
        features['rsi_overbought'] = (rsi.rsi_12 > 70).astype(float)
        
        # 布林帶特徵
        boll = ti.calculate_boll()
        features['boll_upper'] = boll.upper
        features['boll_middle'] = boll.middle
        features['boll_lower'] = boll.lower
        features['boll_position'] = (df['close'] - boll.lower) / (boll.upper - boll.lower)
        features['boll_width'] = boll.bandwidth
        
        # EMA特徵
        ema = ti.calculate_ema()
        features['ema_5'] = ema.ema_5
        features['ema_10'] = ema.ema_10
        features['ema_20'] = ema.ema_20
        features['ema_60'] = ema.ema_60
        features['ema_bullish'] = (ema.ema_5 > ema.ema_10).astype(float)
        
        # 成交量特徵
        vol = ti.calculate_volume_analysis()
        features['obv'] = vol.obv
        features['volume_ma_ratio'] = vol.volume_ratio
        
        return features
    
    def _extract_candlestick_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取K線形態特徵"""
        features = pd.DataFrame(index=df.index)
        
        # 初始化特徵列
        pattern_types = [
            'doji', 'hammer', 'shooting_star', 'engulfing_bullish',
            'engulfing_bearish', 'morning_star', 'evening_star'
        ]
        
        for pattern in pattern_types:
            features[f'pattern_{pattern}'] = 0.0
        
        features['pattern_score'] = 0.0
        features['pattern_bullish'] = 0.0
        features['pattern_bearish'] = 0.0
        
        # 檢測每個位置的形態
        for i in range(len(df)):
            if i < 2:  # 需要至少3根K線
                continue
            
            pattern = self.candlestick_analyzer.detect_at_index(df, i, calculate_scores=True)
            
            if pattern and pattern.pattern_type != PatternType.NONE:
                # 記錄形態類型
                pattern_name = pattern.pattern_type.value.lower()
                if f'pattern_{pattern_name}' in features.columns:
                    features.loc[df.index[i], f'pattern_{pattern_name}'] = 1.0
                
                # 記錄形態分數
                features.loc[df.index[i], 'pattern_score'] = pattern.overall_score / 100.0
                
                # 記錄多空方向
                if pattern.is_bullish():
                    features.loc[df.index[i], 'pattern_bullish'] = 1.0
                elif pattern.is_bearish():
                    features.loc[df.index[i], 'pattern_bearish'] = 1.0
        
        return features
    
    def _extract_sentiment_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取市場情緒特徵"""
        features = pd.DataFrame(index=df.index)
        
        try:
            sentiment = self.sentiment_analyzer.analyze(df)
            
            # 恐懼/貪婪指數
            features['fear_greed_index'] = sentiment.indicators.fear_greed_index / 100
            
            # VIX風格指數
            features['vix_style'] = min(sentiment.indicators.vix_style_index / 50, 1.0)
            
            # 成交量異常
            features['volume_anomaly'] = sentiment.indicators.volume_anomaly_score / 100
            
            # 市場廣度
            features['market_breadth'] = sentiment.indicators.breadth_indicator / 100
            
            # 資金流向
            features['money_flow'] = (sentiment.money_flow.flow_strength + 1) / 2
            
            # 流動性評分
            features['liquidity'] = sentiment.liquidity.liquidity_score / 100
            
            # 市場階段編碼
            phase_map = {
                'accumulation': 0,
                'markup': 1,
                'distribution': 2,
                'markdown': 3
            }
            features['market_phase'] = phase_map.get(sentiment.phase.value, 0)
            
        except Exception as e:
            logger.debug(f"情緒特徵提取失敗: {e}")
            # 填充默認值
            for col in ['fear_greed_index', 'vix_style', 'volume_anomaly', 
                       'market_breadth', 'money_flow', 'liquidity', 'market_phase']:
                features[col] = 0.5
        
        return features
    
    def create_target_variable(
        self,
        df: pd.DataFrame,
        forward_period: int = 5,
        threshold: float = 0.02
    ) -> pd.Series:
        """
        創建目標變量
        
        Args:
            df: 價格數據
            forward_period: 前瞻週期
            threshold: 漲跌閾值
            
        Returns:
            Series: 目標變量 (1: 上漲, 0: 持平, -1: 下跌)
        """
        close = df['close']
        
        # 計算未來收益率
        future_return = (close.shift(-forward_period) - close) / close
        
        # 創建目標變量
        target = pd.Series(0, index=df.index)
        target[future_return > threshold] = 1
        target[future_return < -threshold] = -1
        
        return target
    
    def prepare_ml_dataset(
        self,
        df: pd.DataFrame,
        forward_period: int = 5,
        threshold: float = 0.02,
        drop_na: bool = True
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        準備機器學習數據集
        
        Args:
            df: 原始價格數據
            forward_period: 前瞻週期
            threshold: 漲跌閾值
            drop_na: 是否刪除NaN
            
        Returns:
            (特徵DataFrame, 目標Series)
        """
        # 提取特徵
        features = self.extract_features(df)
        
        # 創建目標變量
        target = self.create_target_variable(df, forward_period, threshold)
        
        # 合併
        dataset = features.copy()
        dataset['target'] = target
        
        if drop_na:
            dataset = dataset.dropna()
        
        X = dataset.drop('target', axis=1)
        y = dataset['target']
        
        return X, y
    
    def fit_scaler(self, X: pd.DataFrame):
        """擬合標準化器"""
        if self.scaler:
            self.scaler.fit(X)
    
    def transform_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """轉換特徵"""
        if self.scaler:
            X_scaled = pd.DataFrame(
                self.scaler.transform(X),
                columns=X.columns,
                index=X.index
            )
            return X_scaled
        return X
    
    def get_feature_importance(self, model, feature_names: List[str]) -> Dict[str, float]:
        """
        獲取特徵重要性
        
        Args:
            model: 訓練好的模型
            feature_names: 特徵名稱列表
            
        Returns:
            特徵重要性字典
        """
        importance = {}
        
        if hasattr(model, 'feature_importances_'):
            # 樹模型
            for name, imp in zip(feature_names, model.feature_importances_):
                importance[name] = imp
        elif hasattr(model, 'coef_'):
            # 線性模型
            for name, coef in zip(feature_names, model.coef_):
                importance[name] = abs(coef)
        
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))


# 便捷函數
def extract_features(df: pd.DataFrame, config: Optional[FeatureConfig] = None) -> pd.DataFrame:
    """便捷函數：提取特徵"""
    engineer = FeatureEngineer(config)
    return engineer.extract_features(df)


def prepare_dataset(
    df: pd.DataFrame,
    forward_period: int = 5,
    threshold: float = 0.02
) -> Tuple[pd.DataFrame, pd.Series]:
    """便捷函數：準備數據集"""
    engineer = FeatureEngineer()
    return engineer.prepare_ml_dataset(df, forward_period, threshold)
