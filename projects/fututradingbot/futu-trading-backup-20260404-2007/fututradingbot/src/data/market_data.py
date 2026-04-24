"""
富途交易機器人 - 資料獲取模組
Market Data Module for Futu Trading Bot

提供功能：
- 連接富途API獲取K線數據
- 數據緩存與管理
- 即時行情訂閱
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Callable, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os
import pickle
from pathlib import Path
import threading
import time
from queue import Queue


class KLType(Enum):
    """K線類型枚舉"""
    K_1M = "K_1M"      # 1分鐘
    K_5M = "K_5M"      # 5分鐘
    K_15M = "K_15M"    # 15分鐘
    K_30M = "K_30M"    # 30分鐘
    K_60M = "K_60M"    # 60分鐘
    K_DAY = "K_DAY"    # 日線
    K_WEEK = "K_WEEK"  # 週線
    K_MON = "K_MON"    # 月線


class SubType(Enum):
    """訂閱類型枚舉"""
    SUBTYPE_NONE = 0
    SUBTYPE_TICKER = 1      # 逐筆
    SUBTYPE_QUOTE = 2       # 報價
    SUBTYPE_ORDER_BOOK = 3  # 擺盤
    SUBTYPE_BROKER = 4      # 經紀隊列
    SUBTYPE_KL_1M = 5       # 1分鐘K線
    SUBTYPE_KL_5M = 6       # 5分鐘K線
    SUBTYPE_KL_15M = 7      # 15分鐘K線
    SUBTYPE_KL_30M = 8      # 30分鐘K線
    SUBTYPE_KL_60M = 9      # 60分鐘K線
    SUBTYPE_KL_DAY = 10     # 日K線


@dataclass
class StockQuote:
    """股票報價數據"""
    code: str                           # 股票代碼
    name: str = ""                      # 股票名稱
    last_price: float = 0.0             # 最新價
    open_price: float = 0.0             # 開盤價
    high_price: float = 0.0             # 最高價
    low_price: float = 0.0              # 最低價
    prev_close: float = 0.0             # 昨收價
    volume: int = 0                     # 成交量
    turnover: float = 0.0               # 成交額
    timestamp: datetime = field(default_factory=datetime.now)
    bid_price: List[float] = field(default_factory=list)   # 買盤價格
    bid_volume: List[int] = field(default_factory=list)    # 買盤數量
    ask_price: List[float] = field(default_factory=list)   # 賣盤價格
    ask_volume: List[int] = field(default_factory=list)    # 賣盤數量


@dataclass
class KLineData:
    """K線數據"""
    code: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover: float
    ktype: KLType


class DataCache:
    """
    數據緩存管理器
    
    提供本地數據緩存功能，減少API調用
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        初始化緩存管理器
        
        Args:
            cache_dir: 緩存目錄路徑
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, pd.DataFrame] = {}
        self._lock = threading.Lock()
    
    def _get_cache_key(self, code: str, ktype: KLType, start: str, end: str) -> str:
        """生成緩存鍵"""
        return f"{code}_{ktype.value}_{start}_{end}"
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """獲取緩存文件路徑"""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def get(
        self, 
        code: str, 
        ktype: KLType, 
        start: str, 
        end: str,
        max_age_hours: int = 24
    ) -> Optional[pd.DataFrame]:
        """
        從緩存獲取數據
        
        Args:
            code: 股票代碼
            ktype: K線類型
            start: 開始日期
            end: 結束日期
            max_age_hours: 緩存最大有效時間(小時)
            
        Returns:
            緩存的DataFrame或None
        """
        cache_key = self._get_cache_key(code, ktype, start, end)
        
        # 先檢查內存緩存 (內存緩存也需要檢查過期時間)
        with self._lock:
            if cache_key in self._memory_cache:
                # 同時檢查文件緩存時間以判斷是否過期
                cache_path = self._get_cache_path(cache_key)
                if cache_path.exists():
                    file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
                    if file_age < timedelta(hours=max_age_hours):
                        return self._memory_cache[cache_key].copy()
                else:
                    # 文件不存在但內存存在，直接返回
                    if max_age_hours > 0:
                        return self._memory_cache[cache_key].copy()
        
        # 檢查文件緩存
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            # 檢查文件年齡
            file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            if file_age < timedelta(hours=max_age_hours):
                try:
                    with open(cache_path, 'rb') as f:
                        df = pickle.load(f)
                    # 存入內存緩存
                    with self._lock:
                        self._memory_cache[cache_key] = df
                    return df.copy()
                except Exception as e:
                    print(f"讀取緩存失敗: {e}")
                    return None
        
        return None
    
    def set(
        self, 
        code: str, 
        ktype: KLType, 
        start: str, 
        end: str, 
        df: pd.DataFrame
    ) -> None:
        """
        設置緩存數據
        
        Args:
            code: 股票代碼
            ktype: K線類型
            start: 開始日期
            end: 結束日期
            df: 要緩存的DataFrame
        """
        cache_key = self._get_cache_key(code, ktype, start, end)
        
        # 存入內存緩存
        with self._lock:
            self._memory_cache[cache_key] = df.copy()
        
        # 存入文件緩存
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(df, f)
        except Exception as e:
            print(f"寫入緩存失敗: {e}")
    
    def clear(self, code: Optional[str] = None) -> None:
        """
        清除緩存
        
        Args:
            code: 指定股票代碼清除，None則清除所有
        """
        with self._lock:
            if code:
                keys_to_remove = [k for k in self._memory_cache.keys() if k.startswith(code)]
                for key in keys_to_remove:
                    del self._memory_cache[key]
            else:
                self._memory_cache.clear()
        
        # 清除文件緩存
        if code:
            for cache_file in self.cache_dir.glob(f"{code}_*.pkl"):
                cache_file.unlink(missing_ok=True)
        else:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink(missing_ok=True)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """獲取緩存信息"""
        with self._lock:
            memory_count = len(self._memory_cache)
        
        file_count = len(list(self.cache_dir.glob("*.pkl")))
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
        
        return {
            'memory_cache_count': memory_count,
            'file_cache_count': file_count,
            'total_cache_size_mb': round(total_size / (1024 * 1024), 2)
        }


class FutuMarketData:
    """
    富途行情數據接口
    
    提供與富途API的連接和數據獲取功能
    注意：實際使用時需要安裝futu-api庫
    """
    
    def __init__(
        self, 
        host: str = "127.0.0.1", 
        port: int = 11111,
        cache_dir: str = "cache"
    ):
        """
        初始化富途行情接口
        
        Args:
            host: OpenD服務器地址
            port: OpenD服務器端口
            cache_dir: 緩存目錄
        """
        self.host = host
        self.port = port
        self.cache = DataCache(cache_dir)
        self._quote_ctx = None
        self._subscribed_codes: set = set()
        self._realtime_callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        self._lock = threading.Lock()
        
    def _get_quote_context(self):
        """獲取行情上下文 (延遲初始化)"""
        if self._quote_ctx is None:
            try:
                from futu import OpenQuoteContext
                self._quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            except ImportError:
                raise ImportError("請安裝futu-api: pip install futu-api")
        return self._quote_ctx
    
    def connect(self) -> bool:
        """
        連接富途OpenD服務
        
        Returns:
            連接是否成功
        """
        try:
            ctx = self._get_quote_context()
            # 測試連接
            ret, data = ctx.get_global_state()
            return ret == 0
        except Exception as e:
            print(f"連接富途API失敗: {e}")
            return False
    
    def disconnect(self) -> None:
        """斷開連接"""
        if self._quote_ctx:
            self._quote_ctx.close()
            self._quote_ctx = None
    
    def get_kline_data(
        self,
        code: str,
        ktype: KLType = KLType.K_DAY,
        start: Optional[str] = None,
        end: Optional[str] = None,
        num: int = 100,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        獲取K線數據
        
        Args:
            code: 股票代碼 (如 "HK.00700")
            ktype: K線類型
            start: 開始日期 (格式: "2024-01-01")
            end: 結束日期 (格式: "2024-12-31")
            num: 獲取數量 (當start/end未指定時使用)
            use_cache: 是否使用緩存
            
        Returns:
            K線數據DataFrame
        """
        # 設置默認日期
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")
        if start is None:
            start_date = datetime.now() - timedelta(days=num)
            start = start_date.strftime("%Y-%m-%d")
        
        # 檢查緩存
        if use_cache:
            cached_df = self.cache.get(code, ktype, start, end)
            if cached_df is not None:
                return cached_df
        
        # 從API獲取數據
        try:
            ctx = self._get_quote_context()
            from futu import KLType as FutuKLType
            
            # 映射K線類型
            ktype_mapping = {
                KLType.K_1M: FutuKLType.K_1M,
                KLType.K_5M: FutuKLType.K_5M,
                KLType.K_15M: FutuKLType.K_15M,
                KLType.K_30M: FutuKLType.K_30M,
                KLType.K_60M: FutuKLType.K_60M,
                KLType.K_DAY: FutuKLType.K_DAY,
                KLType.K_WEEK: FutuKLType.K_WEEK,
                KLType.K_MON: FutuKLType.K_MON,
            }
            
            futu_ktype = ktype_mapping.get(ktype, FutuKLType.K_DAY)
            
            ret, data, page_req_key = ctx.request_history_kline(
                code=code,
                start=start,
                end=end,
                ktype=futu_ktype,
                max_count=num
            )
            
            if ret != 0:
                raise Exception(f"獲取K線數據失敗: {data}")
            
            # 處理數據
            df = self._process_kline_data(data, code, ktype)
            
            # 存入緩存
            if use_cache:
                self.cache.set(code, ktype, start, end, df)
            
            return df
            
        except ImportError:
            # 如果沒有安裝futu-api，返回模擬數據
            print("警告: 未安裝futu-api，返回模擬數據")
            return self._generate_mock_kline_data(code, ktype, start, end, num)
        except Exception as e:
            print(f"獲取K線數據失敗: {e}")
            return pd.DataFrame()
    
    def _process_kline_data(
        self, 
        data: pd.DataFrame, 
        code: str, 
        ktype: KLType
    ) -> pd.DataFrame:
        """處理K線數據"""
        if data.empty:
            return data
        
        # 重命名列以符合標準格式
        column_mapping = {
            'time_key': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'turnover': 'turnover'
        }
        
        df = data.rename(columns=column_mapping)
        
        # 添加股票代碼和K線類型
        df['code'] = code
        df['ktype'] = ktype.value
        
        # 確保timestamp是datetime類型
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def _generate_mock_kline_data(
        self,
        code: str,
        ktype: KLType,
        start: str,
        end: str,
        num: int
    ) -> pd.DataFrame:
        """生成模擬K線數據 (用於測試)"""
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)
        
        # 生成日期範圍
        if ktype == KLType.K_DAY:
            dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 工作日
        elif ktype == KLType.K_WEEK:
            dates = pd.date_range(start=start_date, end=end_date, freq='W')
        elif ktype == KLType.K_MON:
            dates = pd.date_range(start=start_date, end=end_date, freq='M')
        else:
            # 分鐘線
            freq_map = {
                KLType.K_1M: '1min',
                KLType.K_5M: '5min',
                KLType.K_15M: '15min',
                KLType.K_30M: '30min',
                KLType.K_60M: '60min',
            }
            freq = freq_map.get(ktype, '1min')
            dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # 限制數量
        if len(dates) > num:
            dates = dates[-num:]
        
        # 生成價格數據
        np.random.seed(42)  # 為了可重複性
        n = len(dates)
        
        # 隨機遊走生成價格
        returns = np.random.normal(0.001, 0.02, n)
        prices = 100 * np.exp(np.cumsum(returns))
        
        # 生成OHLC
        df = pd.DataFrame({
            'timestamp': dates,
            'code': code,
            'ktype': ktype.value,
            'open': prices * (1 + np.random.normal(0, 0.005, n)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n))),
            'close': prices,
            'volume': np.random.randint(100000, 10000000, n),
            'turnover': np.random.randint(1000000, 100000000, n)
        })
        
        # 確保high >= open, close, low
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        return df
    
    def get_stock_quote(self, code: str) -> Optional[StockQuote]:
        """
        獲取股票實時報價
        
        Args:
            code: 股票代碼
            
        Returns:
            StockQuote對象或None
        """
        try:
            ctx = self._get_quote_context()
            ret, data = ctx.get_stock_snapshot([code])
            
            if ret != 0 or data.empty:
                return None
            
            row = data.iloc[0]
            return StockQuote(
                code=code,
                name=row.get('stock_name', ''),
                last_price=row.get('last_price', 0.0),
                open_price=row.get('open_price', 0.0),
                high_price=row.get('high_price', 0.0),
                low_price=row.get('low_price', 0.0),
                prev_close=row.get('prev_close_price', 0.0),
                volume=row.get('volume', 0),
                turnover=row.get('turnover', 0.0),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"獲取股票報價失敗: {e}")
            return None
    
    def subscribe_realtime(
        self, 
        code: str, 
        sub_type: SubType = SubType.SUBTYPE_QUOTE,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        訂閱實時行情
        
        Args:
            code: 股票代碼
            sub_type: 訂閱類型
            callback: 回調函數
            
        Returns:
            訂閱是否成功
        """
        try:
            ctx = self._get_quote_context()
            from futu import SubType as FutuSubType
            
            # 映射訂閱類型
            subtype_mapping = {
                SubType.SUBTYPE_TICKER: FutuSubType.TICKER,
                SubType.SUBTYPE_QUOTE: FutuSubType.QUOTE,
                SubType.SUBTYPE_ORDER_BOOK: FutuSubType.ORDER_BOOK,
                SubType.SUBTYPE_BROKER: FutuSubType.BROKER,
                SubType.SUBTYPE_KL_1M: FutuSubType.KL_1M,
                SubType.SUBTYPE_KL_5M: FutuSubType.KL_5M,
                SubType.SUBTYPE_KL_15M: FutuSubType.KL_15M,
                SubType.SUBTYPE_KL_30M: FutuSubType.KL_30M,
                SubType.SUBTYPE_KL_60M: FutuSubType.KL_60M,
                SubType.SUBTYPE_KL_DAY: FutuSubType.KL_DAY,
            }
            
            futu_subtype = subtype_mapping.get(sub_type, FutuSubType.QUOTE)
            
            ret, msg = ctx.subscribe(code, [futu_subtype])
            
            if ret == 0:
                with self._lock:
                    self._subscribed_codes.add(code)
                    if callback:
                        if code not in self._realtime_callbacks:
                            self._realtime_callbacks[code] = []
                        self._realtime_callbacks[code].append(callback)
                return True
            else:
                print(f"訂閱失敗: {msg}")
                return False
                
        except Exception as e:
            print(f"訂閱實時行情失敗: {e}")
            return False
    
    def unsubscribe_realtime(self, code: str) -> bool:
        """
        取消訂閱實時行情
        
        Args:
            code: 股票代碼
            
        Returns:
            取消訂閱是否成功
        """
        try:
            ctx = self._get_quote_context()
            ret, msg = ctx.unsubscribe(code)
            
            if ret == 0:
                with self._lock:
                    self._subscribed_codes.discard(code)
                    if code in self._realtime_callbacks:
                        del self._realtime_callbacks[code]
                return True
            else:
                print(f"取消訂閱失敗: {msg}")
                return False
                
        except Exception as e:
            print(f"取消訂閱失敗: {e}")
            return False
    
    def start_realtime_loop(self) -> None:
        """啟動實時數據接收循環"""
        self._running = True
        
        def _receive_loop():
            while self._running:
                try:
                    ctx = self._get_quote_context()
                    ret, data = ctx.get_stock_quote(list(self._subscribed_codes))
                    
                    if ret == 0 and not data.empty:
                        self._process_realtime_data(data)
                    
                    time.sleep(1)  # 每秒檢查一次
                    
                except Exception as e:
                    print(f"實時數據接收錯誤: {e}")
                    time.sleep(5)
        
        self._receive_thread = threading.Thread(target=_receive_loop, daemon=True)
        self._receive_thread.start()
    
    def stop_realtime_loop(self) -> None:
        """停止實時數據接收循環"""
        self._running = False
    
    def _process_realtime_data(self, data: pd.DataFrame) -> None:
        """處理實時數據"""
        for _, row in data.iterrows():
            code = row.get('code')
            if code in self._realtime_callbacks:
                for callback in self._realtime_callbacks[code]:
                    try:
                        callback(row)
                    except Exception as e:
                        print(f"回調執行錯誤: {e}")
    
    def get_subscribed_codes(self) -> List[str]:
        """獲取已訂閱的股票代碼列表"""
        with self._lock:
            return list(self._subscribed_codes)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """獲取緩存信息"""
        return self.cache.get_cache_info()
    
    def clear_cache(self, code: Optional[str] = None) -> None:
        """清除緩存"""
        self.cache.clear(code)


class MarketDataManager:
    """
    市場數據管理器
    
    提供高級數據管理功能
    """
    
    def __init__(self, futu_md: Optional[FutuMarketData] = None):
        """
        初始化市場數據管理器
        
        Args:
            futu_md: FutuMarketData實例
        """
        self.futu_md = futu_md or FutuMarketData()
        self._watchlist: List[str] = []
        self._data_history: Dict[str, pd.DataFrame] = {}
    
    def add_to_watchlist(self, code: str) -> None:
        """添加股票到觀察列表"""
        if code not in self._watchlist:
            self._watchlist.append(code)
    
    def remove_from_watchlist(self, code: str) -> None:
        """從觀察列表移除股票"""
        if code in self._watchlist:
            self._watchlist.remove(code)
    
    def get_watchlist(self) -> List[str]:
        """獲取觀察列表"""
        return self._watchlist.copy()
    
    def fetch_watchlist_data(
        self, 
        ktype: KLType = KLType.K_DAY,
        num: int = 100
    ) -> Dict[str, pd.DataFrame]:
        """
        獲取觀察列表所有股票的數據
        
        Args:
            ktype: K線類型
            num: 獲取數量
            
        Returns:
            股票代碼到DataFrame的映射
        """
        result = {}
        for code in self._watchlist:
            df = self.futu_md.get_kline_data(code, ktype=ktype, num=num)
            if not df.empty:
                result[code] = df
                self._data_history[code] = df
        return result
    
    def get_latest_data(self, code: str) -> Optional[pd.DataFrame]:
        """獲取股票最新數據"""
        return self._data_history.get(code)
    
    def export_data(
        self, 
        code: str, 
        filepath: str, 
        format: str = "csv"
    ) -> bool:
        """
        導出數據到文件
        
        Args:
            code: 股票代碼
            filepath: 文件路徑
            format: 文件格式 (csv, json, parquet)
            
        Returns:
            導出是否成功
        """
        df = self._data_history.get(code)
        if df is None or df.empty:
            return False
        
        try:
            if format.lower() == "csv":
                df.to_csv(filepath, index=False)
            elif format.lower() == "json":
                df.to_json(filepath, orient="records", date_format="iso")
            elif format.lower() == "parquet":
                df.to_parquet(filepath, index=False)
            else:
                raise ValueError(f"不支持的格式: {format}")
            return True
        except Exception as e:
            print(f"導出數據失敗: {e}")
            return False
    
    def calculate_zscore_realtime(
        self, 
        code: str, 
        period: int = 60,
        price_col: str = 'close'
    ) -> Optional[pd.Series]:
        """
        實時計算Z-Score
        
        從緩存數據中計算Z-Score，用於實時交易決策
        
        Args:
            code: 股票代碼
            period: Z-Score計算週期
            price_col: 價格列名
            
        Returns:
            Z-Score序列，無數據則返回None
            
        Example:
            >>> md = MarketDataManager()
            >>> md.fetch_watchlist_data()  # 先獲取數據
            >>> zscore = md.calculate_zscore_realtime("HK.00700")
            >>> print(f"當前Z-Score: {zscore.iloc[-1]:.2f}")
        """
        from src.indicators.technical import calculate_zscore
        
        df = self._data_history.get(code)
        if df is None or df.empty:
            print(f"[Z-Score] 無 {code} 的緩存數據")
            return None
        
        if price_col not in df.columns:
            print(f"[Z-Score] 數據中無 {price_col} 列")
            return None
        
        # 計算Z-Score
        zscore = calculate_zscore(df[price_col], period=period)
        
        return zscore
    
    def get_zscore_signal(
        self, 
        code: str,
        upper_threshold: float = 2.0,
        lower_threshold: float = -2.0,
        period: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        獲取Z-Score交易信號
        
        返回當前Z-Score值及交易建議
        
        Args:
            code: 股票代碼
            upper_threshold: 上閾值 (超買)
            lower_threshold: 下閾值 (超賣)
            period: 計算週期
            
        Returns:
            信號字典，包含:
            - zscore: 當前Z-Score值
            - signal: 交易信號 (1=做多, -1=做空, 0=觀望)
            - ma: 移動平均價
            - price: 當前價格
            - deviation: 偏離程度 (%)
        """
        from src.indicators.technical import calculate_zscore_advanced
        
        df = self._data_history.get(code)
        if df is None or df.empty:
            return None
        
        # 計算Z-Score
        result = calculate_zscore_advanced(
            df, 
            period=period,
            upper_threshold=upper_threshold,
            lower_threshold=lower_threshold
        )
        
        if result.zscore.empty:
            return None
        
        # 獲取最新值
        latest_zscore = result.zscore.iloc[-1]
        latest_ma = result.ma.iloc[-1]
        latest_price = df['close'].iloc[-1]
        
        # 生成信號
        signal = 0
        if latest_zscore < lower_threshold:
            signal = 1  # 超賣，做多
        elif latest_zscore > upper_threshold:
            signal = -1  # 超買，做空
        
        # 計算偏離程度
        deviation = (latest_price - latest_ma) / latest_ma * 100
        
        return {
            'code': code,
            'zscore': round(latest_zscore, 2),
            'signal': signal,
            'signal_text': '做多' if signal == 1 else ('做空' if signal == -1 else '觀望'),
            'ma': round(latest_ma, 2),
            'price': round(latest_price, 2),
            'deviation': round(deviation, 2),
            'threshold_upper': upper_threshold,
            'threshold_lower': lower_threshold
        }
