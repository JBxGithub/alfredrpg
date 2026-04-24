"""
策略進化器 - Strategy Evolver

基於交易結果自動進化策略參數
"""

import json
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from src.utils.logger import logger
from src.realtime_optimizer.performance_tracker import PerformanceTracker, PerformanceMetrics


@dataclass
class StrategyGene:
    """策略基因（參數組合）"""
    params: Dict[str, Any]
    fitness_score: float = 0.0
    generation: int = 0
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class StrategyEvolver:
    """
    策略進化器
    
    使用遺傳算法概念：
    - 保留表現良好的參數組合
    - 交叉組合產生新參數
    - 適度變異探索新空間
    """
    
    def __init__(
        self,
        population_size: int = 10,
        mutation_rate: float = 0.1,
        elite_ratio: float = 0.2
    ):
        """
        初始化
        
        Args:
            population_size: 種群大小（保留多少組參數）
            mutation_rate: 變異率
            elite_ratio: 精英比例（直接保留的頂級參數）
        """
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.elite_ratio = elite_ratio
        
        self.population: List[StrategyGene] = []
        self.generation = 0
        self.best_gene: Optional[StrategyGene] = None
        
        # 參數範圍定義
        self.param_ranges = {
            'position_size': (0.01, 0.10),
            'stop_loss_pct': (0.005, 0.05),
            'take_profit_pct': (0.01, 0.10),
            'entry_threshold': (0.1, 0.5),
            'exit_threshold': (0.1, 0.5)
        }
    
    def initialize_population(self, base_params: Dict[str, Any]):
        """
        初始化種群
        
        Args:
            base_params: 基礎參數
        """
        self.population = []
        
        # 添加基礎參數
        self.population.append(StrategyGene(
            params=base_params.copy(),
            generation=0
        ))
        
        # 生成變異版本
        for i in range(self.population_size - 1):
            mutated = self._mutate(base_params, strength=0.3)
            self.population.append(StrategyGene(
                params=mutated,
                generation=0
            ))
        
        logger.info(f"初始化種群: {len(self.population)} 個基因")
    
    def evaluate_generation(self, tracker: PerformanceTracker):
        """
        評估當前一代的表現
        
        Args:
            tracker: 表現追踪器
        """
        metrics = tracker.get_metrics()
        
        # 計算適應度分數
        for gene in self.population:
            gene.fitness_score = self._calculate_fitness(metrics, gene.params)
        
        # 排序
        self.population.sort(key=lambda x: x.fitness_score, reverse=True)
        
        # 更新最佳基因
        if self.population:
            self.best_gene = self.population[0]
            logger.info(
                f"第 {self.generation} 代最佳適應度: {self.best_gene.fitness_score:.4f}"
            )
    
    def _calculate_fitness(
        self,
        metrics: PerformanceMetrics,
        params: Dict[str, Any]
    ) -> float:
        """
        計算適應度分數
        
        綜合考慮：
        - 總回報
        - 夏普比率
        - 勝率
        - 最大回撤
        """
        if metrics.total_trades < 5:
            return 0.0
        
        # 各項得分
        return_score = min(metrics.total_pnl_pct / 10, 1.0)  # 回報 (10% = 滿分)
        sharpe_score = min(metrics.sharpe_ratio / 2, 1.0)     # 夏普 (2 = 滿分)
        winrate_score = metrics.win_rate                      # 勝率
        drawdown_score = 1 - metrics.max_drawdown / 0.20      # 回撤 (20% = 0分)
        
        # 加權平均
        fitness = (
            return_score * 0.3 +
            sharpe_score * 0.3 +
            winrate_score * 0.2 +
            drawdown_score * 0.2
        )
        
        return max(0, fitness)
    
    def evolve(self) -> StrategyGene:
        """
        進化一代
        
        Returns:
            最佳基因
        """
        self.generation += 1
        
        # 保留精英
        elite_count = int(self.population_size * self.elite_ratio)
        new_population = self.population[:elite_count]
        
        # 交叉產生新一代
        while len(new_population) < self.population_size:
            parent1 = self._select_parent()
            parent2 = self._select_parent()
            
            child_params = self._crossover(parent1.params, parent2.params)
            child_params = self._mutate(child_params)
            
            new_population.append(StrategyGene(
                params=child_params,
                generation=self.generation
            ))
        
        self.population = new_population
        logger.info(f"進化到第 {self.generation} 代")
        
        return self.population[0]
    
    def _select_parent(self) -> StrategyGene:
        """選擇父代（輪盤賭選擇）"""
        fitnesses = [g.fitness_score for g in self.population]
        total_fitness = sum(fitnesses)
        
        if total_fitness == 0:
            return np.random.choice(self.population)
        
        probs = [f / total_fitness for f in fitnesses]
        return np.random.choice(self.population, p=probs)
    
    def _crossover(
        self,
        params1: Dict[str, Any],
        params2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """交叉兩個參數組合"""
        child = {}
        for key in params1:
            if key in params2:
                # 隨機選擇父代基因
                child[key] = params1[key] if np.random.random() < 0.5 else params2[key]
            else:
                child[key] = params1[key]
        return child
    
    def _mutate(
        self,
        params: Dict[str, Any],
        strength: float = None
    ) -> Dict[str, Any]:
        """變異參數"""
        if strength is None:
            strength = self.mutation_rate
        
        mutated = params.copy()
        
        for key, value in mutated.items():
            if key in self.param_ranges and np.random.random() < strength:
                min_val, max_val = self.param_ranges[key]
                
                # 高斯變異
                mutation = np.random.normal(0, (max_val - min_val) * 0.1)
                mutated[key] = np.clip(value + mutation, min_val, max_val)
        
        return mutated
    
    def get_best_params(self) -> Dict[str, Any]:
        """獲取最佳參數"""
        if self.best_gene:
            return self.best_gene.params.copy()
        return {}
    
    def get_population_stats(self) -> Dict[str, Any]:
        """獲取種群統計"""
        if not self.population:
            return {}
        
        fitnesses = [g.fitness_score for g in self.population]
        
        return {
            'generation': self.generation,
            'population_size': len(self.population),
            'best_fitness': max(fitnesses),
            'avg_fitness': np.mean(fitnesses),
            'worst_fitness': min(fitnesses),
            'best_params': self.best_gene.params if self.best_gene else None
        }
    
    def save_state(self, filepath: str):
        """保存狀態"""
        state = {
            'generation': self.generation,
            'population': [asdict(g) for g in self.population],
            'best_gene': asdict(self.best_gene) if self.best_gene else None
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"進化狀態已保存: {filepath}")
    
    def load_state(self, filepath: str):
        """加載狀態"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.generation = state['generation']
        self.population = [
            StrategyGene(**g) for g in state['population']
        ]
        
        if state['best_gene']:
            self.best_gene = StrategyGene(**state['best_gene'])
        
        logger.info(f"進化狀態已加載: {filepath}")
