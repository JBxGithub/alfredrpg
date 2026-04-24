"""
性能測試模組 - 測試系統性能
"""

import time
import psutil
import asyncio
from typing import Dict, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class PerformanceMetrics:
    """性能指標"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    response_time_ms: float
    throughput: float  # 每秒處理數據量
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceMonitor:
    """性能監控器"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history = 1000
        self.start_time = time.time()
        self.request_count = 0
        self.total_response_time = 0
    
    def record_request(self, response_time: float):
        """記錄請求響應時間"""
        self.request_count += 1
        self.total_response_time += response_time
    
    def get_metrics(self) -> PerformanceMetrics:
        """獲取當前性能指標"""
        process = psutil.Process()
        
        # 計算平均響應時間
        avg_response_time = (
            self.total_response_time / self.request_count * 1000
            if self.request_count > 0 else 0
        )
        
        # 計算吞吐量（運行時間內的請求數）
        elapsed = time.time() - self.start_time
        throughput = self.request_count / elapsed if elapsed > 0 else 0
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=process.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            memory_mb=process.memory_info().rss / 1024 / 1024,
            response_time_ms=avg_response_time,
            throughput=throughput
        )
        
        # 保存歷史記錄
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        return metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        if not self.metrics_history:
            return {'status': 'no_data'}
        
        recent = self.metrics_history[-100:]  # 最近 100 條記錄
        
        return {
            'status': 'ok',
            'uptime_seconds': time.time() - self.start_time,
            'total_requests': self.request_count,
            'avg_cpu': sum(m.cpu_percent for m in recent) / len(recent),
            'avg_memory': sum(m.memory_percent for m in recent) / len(recent),
            'avg_response_time_ms': sum(m.response_time_ms for m in recent) / len(recent),
            'current_throughput': recent[-1].throughput if recent else 0
        }
    
    def benchmark(self, func: Callable, iterations: int = 100) -> Dict[str, Any]:
        """基準測試"""
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 轉換為毫秒
        
        return {
            'iterations': iterations,
            'avg_ms': sum(times) / len(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'total_ms': sum(times)
        }


async def async_benchmark(func: Callable, iterations: int = 100) -> Dict[str, Any]:
    """異步基準測試"""
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        await func()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    return {
        'iterations': iterations,
        'avg_ms': sum(times) / len(times),
        'min_ms': min(times),
        'max_ms': max(times),
        'total_ms': sum(times)
    }
