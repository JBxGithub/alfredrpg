"""
策略選擇器 - Strategy Selector

根據市場狀態選擇最適合的策略
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from src.utils.logger import logger
from src.adaptive_strategy.market_regime_detector import MarketRegime, RegimeMetrics


@dataclass
class StrategyScore:
    """策略評分"""
    strategy_name: str
    score: float
    regime_fit: float      # 適合當前狀態程度
    historical_performance: float  # 歷史表現
    risk_adjusted_return: float    # 風險調整回報
    reason: str


class StrategySelector:
    """
    策略選擇器
    
    根據市場狀態動態選擇最佳策略
    """
    
    def __init__(self):
        """初始化"""
        # 策略適配表：哪種策略適合哪種市場狀態
        self.strategy_regime_fit = {
            # 趨勢策略
            'TQQQ_Momentum': {
                MarketRegime.TRENDING_UP: 0.9,
                MarketRegime.TRENDING_DOWN: 0.7,
                MarketRegime.RANGING: 0.3,
                MarketRegime.HIGH_VOLATILITY: 0.4,
                MarketRegime.LOW_VOLATILITY: 0.6,
            },
            # 均值回歸策略
            'MeanReversion': {
                MarketRegime.TRENDING_UP: 0.3,
                MarketRegime.TRENDING_DOWN: 0.3,
                MarketRegime.RANGING: 0.9,
                MarketRegime.HIGH_VOLATILITY: 0.5,
                MarketRegime.LOW_VOLATILITY: 0.8,
            },
            # 突破策略
            'Breakout': {
                MarketRegime.TRENDING_UP: 0.8,
                MarketRegime.TRENDING_DOWN: 0.8,
                MarketRegime.RANGING: 0.4,
                MarketRegime.HIGH_VOLATILITY: 0.7,
                MarketRegime.LOW_VOLATILITY: 0.3,
            },
            # 波動率策略
            'Volatility': {
                MarketRegime.TRENDING_UP: 0.4,
                MarketRegime.TRENDING_DOWN: 0.4,
                MarketRegime.RANGING: 0.5,
                MarketRegime.HIGH_VOLATILITY: 0.9,
                MarketRegime.LOW_VOLATILITY: 0.2,
            },
        }
        
        # 策略歷史表現記錄
        self.strategy_performance: Dict[str, Dict[str, float]] = {}
        
        # 當前選擇
        self.current_strategy: Optional[str] = None
        self.selection_history: List[Dict[str, Any]] = []
    
    def register_strategy(
        self,
        strategy_name: str,
        regime_fit: Dict[MarketRegime, float],
        initial_performance: float = 0.5
    ):
        """
        註冊新策略
        
        Args:
            strategy_name: 策略名稱
            regime_fit: 狀態適配分數
            initial_performance: 初始表現分數
        """
        self.strategy_regime_fit[strategy_name] = regime_fit
        self.strategy_performance[strategy_name] = {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'win_rate': 0.5,
            'max_drawdown': 0.0,
            'score': initial_performance
        }
        logger.info(f"註冊策略: {strategy_name}")
    
    def select_strategy(
        self,
        regime_metrics: RegimeMetrics,
        available_strategies: List[str] = None
    ) -> StrategyScore:
        """
        選擇最佳策略
        
        Args:
            regime_metrics: 市場狀態指標
            available_strategies: 可用策略列表
            
        Returns:
            StrategyScore: 最佳策略評分
        """
        if available_strategies is None:
            available_strategies = list(self.strategy_regime_fit.keys())
        
        current_regime = regime_metrics.regime
        scores: List[StrategyScore] = []
        
        for strategy_name in available_strategies:
            if strategy_name not in self.strategy_regime_fit:
                continue
            
            # 計算狀態適配分數
            regime_fit = self.strategy_regime_fit[strategy_name].get(
                current_regime, 0.5
            )
            
            # 獲取歷史表現
            perf = self.strategy_performance.get(strategy_name, {})
            historical_perf = perf.get('score', 0.5)
            
            # 計算風險調整回報
            risk_adjusted = self._calculate_risk_adjusted_return(perf)
            
            # 綜合評分
            total_score = (
                regime_fit * 0.4 +           # 狀態適配 40%
                historical_perf * 0.35 +     # 歷史表現 35%
                risk_adjusted * 0.25         # 風險調整 25%
            )
            
            score = StrategyScore(
                strategy_name=strategy_name,
                score=total_score,
                regime_fit=regime_fit,
                historical_performance=historical_perf,
                risk_adjusted_return=risk_adjusted,
                reason=f"狀態適配: {regime_fit:.2f}, 歷史表現: {historical_perf:.2f}"
            )
            scores.append(score)
        
        # 排序並選擇最佳
        scores.sort(key=lambda x: x.score, reverse=True)
        best = scores[0] if scores else None
        
        if best:
            self.current_strategy = best.strategy_name
            self.selection_history.append({
                'timestamp': datetime.now().isoformat(),
                'regime': current_regime.value,
                'selected_strategy': best.strategy_name,
                'score': best.score,
                'all_scores': [
                    {'name': s.strategy_name, 'score': s.score}
                    for s in scores
                ]
            })
            
            logger.info(
                f"選擇策略: {best.strategy_name} "
                f"(評分: {best.score:.3f}, 狀態: {current_regime.value})"
            )
        
        return best
    
    def _calculate_risk_adjusted_return(
        self,
        performance: Dict[str, float]
    ) -> float:
        """計算風險調整回報"""
        total_return = performance.get('total_return', 0)
        max_dd = performance.get('max_drawdown', 0.01)
        
        if max_dd == 0:
            return 0
        
        # 簡化版 Calmar Ratio
        return total_return / max_dd
    
    def update_strategy_performance(
        self,
        strategy_name: str,
        performance: Dict[str, float]
    ):
        """
        更新策略表現
        
        Args:
            strategy_name: 策略名稱
            performance: 表現指標
        """
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = {}
        
        # 更新各項指標
        for key, value in performance.items():
            self.strategy_performance[strategy_name][key] = value
        
        # 重新計算綜合分數
        perf = self.strategy_performance[strategy_name]
        perf['score'] = self._calculate_performance_score(perf)
        
        logger.info(
            f"更新策略表現: {strategy_name}, "
            f"新分數: {perf['score']:.3f}"
        )
    
    def _calculate_performance_score(
        self,
        performance: Dict[str, float]
    ) -> float:
        """計算綜合表現分數"""
        total_return = performance.get('total_return', 0)
        sharpe = performance.get('sharpe_ratio', 0)
        win_rate = performance.get('win_rate', 0.5)
        max_dd = performance.get('max_drawdown', 0.1)
        
        # 各項加權
        return_score = min(1.0, max(0, total_return / 0.2))  # 20% 回報 = 滿分
        sharpe_score = min(1.0, sharpe / 2.0)                # Sharpe 2 = 滿分
        winrate_score = win_rate
        dd_score = 1.0 - min(1.0, max_dd / 0.2)             # 回撤越小越好
        
        return (
            return_score * 0.3 +
            sharpe_score * 0.25 +
            winrate_score * 0.25 +
            dd_score * 0.2
        )
    
    def get_current_strategy(self) -> Optional[str]:
        """獲取當前策略"""
        return self.current_strategy
    
    def get_strategy_rankings(self) -> List[StrategyScore]:
        """獲取策略排名"""
        scores = []
        for name, perf in self.strategy_performance.items():
            score = StrategyScore(
                strategy_name=name,
                score=perf.get('score', 0),
                regime_fit=0,
                historical_performance=perf.get('score', 0),
                risk_adjusted_return=0,
                reason="基於歷史表現"
            )
            scores.append(score)
        
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores
    
    def should_switch_strategy(
        self,
        new_regime: MarketRegime,
        min_hold_periods: int = 5
    ) -> bool:
        """
        判斷是否應該切換策略
        
        Args:
            new_regime: 新市場狀態
            min_hold_periods: 最小持有週期
            
        Returns:
            是否應該切換
        """
        if len(self.selection_history) < min_hold_periods:
            return True
        
        # 檢查最近是否已經切換過
        recent_switches = sum(
            1 for i in range(1, min_hold_periods)
            if self.selection_history[-i]['selected_strategy'] != 
               self.selection_history[-i-1]['selected_strategy']
        )
        
        # 如果最近頻繁切換，暫時不換
        if recent_switches >= 2:
            logger.warning("最近切換過於頻繁，暫時保持當前策略")
            return False
        
        return True
