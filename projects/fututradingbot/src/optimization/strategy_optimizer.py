"""
策略優化器 - Strategy Optimizer

參數優化 (網格搜索/貝葉斯優化)
Walk-forward 分析
過擬合檢測

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import product
import json
import warnings

from src.strategies.base import BaseStrategy
from src.backtest.enhanced_backtest import EnhancedBacktestEngine, EnhancedBacktestResult
from src.utils.logger import logger

warnings.filterwarnings('ignore')


@dataclass
class OptimizationResult:
    """優化結果"""
    params: Dict[str, Any]
    performance: EnhancedBacktestResult
    score: float
    rank: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'params': self.params,
            'score': self.score,
            'rank': self.rank,
            'performance': self.performance.to_dict() if self.performance else {}
        }


@dataclass
class WalkForwardResult:
    """Walk-forward分析結果"""
    window_results: List[EnhancedBacktestResult]
    consistency_score: float
    avg_return: float
    avg_sharpe: float
    max_drawdown_std: float
    is_stable: bool


class StrategyOptimizer:
    """
    策略優化器
    
    提供參數優化和穩健性測試功能
    """
    
    def __init__(
        self,
        strategy_class: type,
        data: Dict[str, pd.DataFrame],
        initial_capital: float = 1000000.0
    ):
        """
        初始化策略優化器
        
        Args:
            strategy_class: 策略類
            data: 歷史數據
            initial_capital: 初始資金
        """
        self.strategy_class = strategy_class
        self.data = data
        self.initial_capital = initial_capital
        
        self.optimization_results: List[OptimizationResult] = []
        self.best_params: Optional[Dict[str, Any]] = None
        self.best_score: float = -np.inf
        
    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        metric: str = "sharpe_ratio",
        verbose: bool = True
    ) -> List[OptimizationResult]:
        """
        網格搜索參數優化
        
        Args:
            param_grid: 參數網格
            metric: 優化目標指標
            verbose: 是否打印進度
            
        Returns:
            優化結果列表
        """
        logger.info(f"開始網格搜索 | 參數組合數: {self._count_combinations(param_grid)}")
        
        results = []
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        total = self._count_combinations(param_grid)
        count = 0
        
        for values in product(*param_values):
            params = dict(zip(param_names, values))
            count += 1
            
            if verbose and count % 10 == 0:
                logger.info(f"進度: {count}/{total} ({count/total*100:.1f}%)")
            
            try:
                # 運行回測
                result = self._evaluate_params(params)
                
                if result:
                    score = self._calculate_score(result, metric)
                    opt_result = OptimizationResult(
                        params=params,
                        performance=result,
                        score=score
                    )
                    results.append(opt_result)
                    
                    # 更新最佳參數
                    if score > self.best_score:
                        self.best_score = score
                        self.best_params = params
                        
            except Exception as e:
                logger.debug(f"參數評估失敗 {params}: {e}")
                continue
        
        # 排序結果
        results.sort(key=lambda x: x.score, reverse=True)
        for i, r in enumerate(results):
            r.rank = i + 1
        
        self.optimization_results = results
        
        logger.info(f"網格搜索完成 | 最佳分數: {self.best_score:.4f}")
        if self.best_params:
            logger.info(f"最佳參數: {self.best_params}")
        
        return results
    
    def random_search(
        self,
        param_distributions: Dict[str, Tuple[float, float]],
        n_iter: int = 100,
        metric: str = "sharpe_ratio",
        verbose: bool = True
    ) -> List[OptimizationResult]:
        """
        隨機搜索參數優化
        
        Args:
            param_distributions: 參數分布 (min, max)
            n_iter: 迭代次數
            metric: 優化目標指標
            verbose: 是否打印進度
            
        Returns:
            優化結果列表
        """
        logger.info(f"開始隨機搜索 | 迭代次數: {n_iter}")
        
        results = []
        
        for i in range(n_iter):
            if verbose and i % 10 == 0:
                logger.info(f"進度: {i}/{n_iter} ({i/n_iter*100:.1f}%)")
            
            # 隨機採樣參數
            params = {}
            for param_name, (min_val, max_val) in param_distributions.items():
                if isinstance(min_val, int):
                    params[param_name] = np.random.randint(min_val, max_val + 1)
                else:
                    params[param_name] = np.random.uniform(min_val, max_val)
            
            try:
                result = self._evaluate_params(params)
                
                if result:
                    score = self._calculate_score(result, metric)
                    opt_result = OptimizationResult(
                        params=params,
                        performance=result,
                        score=score
                    )
                    results.append(opt_result)
                    
                    if score > self.best_score:
                        self.best_score = score
                        self.best_params = params
                        
            except Exception as e:
                logger.debug(f"參數評估失敗 {params}: {e}")
                continue
        
        results.sort(key=lambda x: x.score, reverse=True)
        for i, r in enumerate(results):
            r.rank = i + 1
        
        self.optimization_results = results
        
        logger.info(f"隨機搜索完成 | 最佳分數: {self.best_score:.4f}")
        return results
    
    def walk_forward_analysis(
        self,
        params: Optional[Dict[str, Any]] = None,
        train_size: int = 252,
        test_size: int = 63,
        step_size: int = 21
    ) -> WalkForwardResult:
        """
        Walk-forward分析
        
        Args:
            params: 策略參數
            train_size: 訓練集大小 (天數)
            test_size: 測試集大小 (天數)
            step_size: 步長 (天數)
            
        Returns:
            WalkForwardResult: Walk-forward分析結果
        """
        logger.info(f"開始Walk-forward分析 | 訓練: {train_size}, 測試: {test_size}")
        
        # 獲取所有日期
        all_dates = set()
        for df in self.data.values():
            all_dates.update(df.index.tolist())
        all_dates = sorted(list(all_dates))
        
        window_results = []
        
        # 滑動窗口
        for i in range(0, len(all_dates) - train_size - test_size, step_size):
            train_start = i
            train_end = i + train_size
            test_start = train_end
            test_end = min(test_start + test_size, len(all_dates))
            
            train_dates = all_dates[train_start:train_end]
            test_dates = all_dates[test_start:test_end]
            
            if len(test_dates) < 10:
                continue
            
            # 準備數據
            test_data = self._filter_data_by_dates(self.data, test_dates)
            
            # 運行回測
            try:
                strategy = self.strategy_class(config=params)
                engine = EnhancedBacktestEngine(strategy, initial_capital=self.initial_capital)
                result = engine.run(test_data)
                window_results.append(result)
            except Exception as e:
                logger.debug(f"窗口回測失敗: {e}")
                continue
        
        # 計算穩定性指標
        if len(window_results) >= 3:
            returns = [r.total_return_pct for r in window_results]
            sharpes = [r.sharpe_ratio for r in window_results]
            drawdowns = [r.max_drawdown_pct for r in window_results]
            
            consistency_score = 1 - (np.std(returns) / (np.mean(np.abs(returns)) + 1e-6))
            avg_return = np.mean(returns)
            avg_sharpe = np.mean(sharpes)
            max_dd_std = np.std(drawdowns)
            
            # 穩定性判斷
            is_stable = (
                consistency_score > 0.5 and
                avg_sharpe > 0.5 and
                max_dd_std < 5.0
            )
        else:
            consistency_score = 0
            avg_return = 0
            avg_sharpe = 0
            max_dd_std = 0
            is_stable = False
        
        wf_result = WalkForwardResult(
            window_results=window_results,
            consistency_score=consistency_score,
            avg_return=avg_return,
            avg_sharpe=avg_sharpe,
            max_drawdown_std=max_dd_std,
            is_stable=is_stable
        )
        
        logger.info(f"Walk-forward分析完成 | 窗口數: {len(window_results)}, 穩定性: {is_stable}")
        
        return wf_result
    
    def detect_overfitting(
        self,
        in_sample_results: List[OptimizationResult],
        out_of_sample_results: List[OptimizationResult],
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        檢測過擬合
        
        Args:
            in_sample_results: 樣本內結果
            out_of_sample_results: 樣本外結果
            threshold: 過擬合閾值
            
        Returns:
            過擬合檢測結果
        """
        if not in_sample_results or not out_of_sample_results:
            return {'is_overfitted': False, 'reason': 'insufficient_data'}
        
        # 計算樣本內和樣本外性能差異
        in_sample_scores = [r.score for r in in_sample_results]
        out_sample_scores = [r.score for r in out_of_sample_results]
        
        in_sample_avg = np.mean(in_sample_scores)
        out_sample_avg = np.mean(out_sample_scores)
        
        # 性能下降比例
        performance_drop = (in_sample_avg - out_sample_avg) / (abs(in_sample_avg) + 1e-6)
        
        # 判斷過擬合
        is_overfitted = performance_drop > threshold
        
        # 找出最穩健的參數
        robust_params = None
        min_performance_diff = float('inf')
        
        for in_r in in_sample_results[:10]:  # 只檢查前10名
            # 找到對應的樣本外結果
            for out_r in out_of_sample_results:
                if in_r.params == out_r.params:
                    diff = abs(in_r.score - out_r.score)
                    if diff < min_performance_diff:
                        min_performance_diff = diff
                        robust_params = in_r.params
                    break
        
        return {
            'is_overfitted': is_overfitted,
            'performance_drop': performance_drop,
            'in_sample_avg': in_sample_avg,
            'out_sample_avg': out_sample_avg,
            'robust_params': robust_params,
            'threshold': threshold
        }
    
    def monte_carlo_simulation(
        self,
        params: Optional[Dict[str, Any]] = None,
        n_simulations: int = 1000,
        perturbation_pct: float = 0.1
    ) -> Dict[str, Any]:
        """
        蒙特卡洛模擬
        
        Args:
            params: 策略參數
            n_simulations: 模擬次數
            perturbation_pct: 參數擾動比例
            
        Returns:
            模擬結果
        """
        logger.info(f"開始蒙特卡洛模擬 | 次數: {n_simulations}")
        
        if params is None:
            params = self.best_params or {}
        
        scores = []
        
        for i in range(n_simulations):
            # 擾動參數
            perturbed_params = {}
            for key, value in params.items():
                if isinstance(value, (int, float)):
                    perturbation = np.random.uniform(-perturbation_pct, perturbation_pct)
                    perturbed_params[key] = value * (1 + perturbation)
                    if isinstance(value, int):
                        perturbed_params[key] = int(perturbed_params[key])
                else:
                    perturbed_params[key] = value
            
            try:
                result = self._evaluate_params(perturbed_params)
                if result:
                    score = self._calculate_score(result, "sharpe_ratio")
                    scores.append(score)
            except Exception:
                continue
        
        if not scores:
            return {'status': 'failed', 'reason': 'no_valid_simulations'}
        
        return {
            'mean_score': np.mean(scores),
            'std_score': np.std(scores),
            'min_score': np.min(scores),
            'max_score': np.max(scores),
            'percentile_5': np.percentile(scores, 5),
            'percentile_95': np.percentile(scores, 95),
            'sharpe_of_strategy': np.mean(scores) / (np.std(scores) + 1e-6),
            'n_simulations': len(scores)
        }
    
    def _evaluate_params(self, params: Dict[str, Any]) -> Optional[EnhancedBacktestResult]:
        """評估參數組合"""
        try:
            strategy = self.strategy_class(config=params)
            engine = EnhancedBacktestEngine(strategy, initial_capital=self.initial_capital)
            result = engine.run(self.data)
            return result
        except Exception as e:
            logger.debug(f"參數評估失敗: {e}")
            return None
    
    def _calculate_score(self, result: EnhancedBacktestResult, metric: str) -> float:
        """計算優化分數"""
        if metric == "sharpe_ratio":
            return result.sharpe_ratio
        elif metric == "total_return":
            return result.total_return_pct
        elif metric == "calmar_ratio":
            return result.calmar_ratio
        elif metric == "win_rate":
            return result.win_rate
        elif metric == "profit_factor":
            return result.profit_factor
        elif metric == "composite":
            # 綜合評分
            score = (
                result.sharpe_ratio * 0.3 +
                result.total_return_pct / 100 * 0.3 +
                result.win_rate / 100 * 0.2 +
                (1 + result.max_drawdown_pct / 100) * 0.2
            )
            return score
        else:
            return result.sharpe_ratio
    
    def _count_combinations(self, param_grid: Dict[str, List[Any]]) -> int:
        """計算參數組合數"""
        count = 1
        for values in param_grid.values():
            count *= len(values)
        return count
    
    def _filter_data_by_dates(
        self,
        data: Dict[str, pd.DataFrame],
        dates: List[datetime]
    ) -> Dict[str, pd.DataFrame]:
        """按日期過濾數據"""
        filtered = {}
        for code, df in data.items():
            mask = df.index.isin(dates)
            filtered_df = df[mask]
            if not filtered_df.empty:
                filtered[code] = filtered_df
        return filtered
    
    def get_optimization_report(self) -> str:
        """生成優化報告"""
        report = []
        report.append("# 策略優化報告\n")
        report.append(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if self.best_params:
            report.append("## 最佳參數\n")
            report.append(f"```json\n{json.dumps(self.best_params, indent=2)}\n```\n\n")
            report.append(f"**最佳分數**: {self.best_score:.4f}\n\n")
        
        if self.optimization_results:
            report.append("## 前10名結果\n")
            report.append("| 排名 | 分數 | 夏普比率 | 總收益 | 勝率 |\n")
            report.append("|------|------|----------|--------|------|\n")
            
            for r in self.optimization_results[:10]:
                perf = r.performance
                report.append(f"| {r.rank} | {r.score:.4f} | {perf.sharpe_ratio:.2f} | {perf.total_return_pct:.2f}% | {perf.win_rate:.1f}% |\n")
            
            report.append("\n")
        
        return ''.join(report)


# 便捷函數
def optimize_strategy(
    strategy_class: type,
    data: Dict[str, pd.DataFrame],
    param_grid: Dict[str, List[Any]],
    metric: str = "sharpe_ratio"
) -> Tuple[Dict[str, Any], List[OptimizationResult]]:
    """
    便捷函數：優化策略
    
    Args:
        strategy_class: 策略類
        data: 歷史數據
        param_grid: 參數網格
        metric: 優化目標
        
    Returns:
        (最佳參數, 所有結果)
    """
    optimizer = StrategyOptimizer(strategy_class, data)
    results = optimizer.grid_search(param_grid, metric)
    return optimizer.best_params, results
