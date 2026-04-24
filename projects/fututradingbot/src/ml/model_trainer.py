"""
模型訓練模組 - Model Trainer

隨機森林模型 (Random Forest)
梯度提升模型 (XGBoost/LightGBM)
模型評估與選擇

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import json
import pickle
import warnings

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        classification_report, confusion_matrix, roc_auc_score
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RandomForestClassifier = None
    GradientBoostingClassifier = None

from src.ml.feature_engineering import FeatureEngineer
from src.utils.logger import logger

warnings.filterwarnings('ignore')


@dataclass
class ModelConfig:
    """模型配置"""
    model_type: str = "random_forest"  # random_forest, xgboost, lightgbm
    test_size: float = 0.2
    random_state: int = 42
    cv_folds: int = 5
    
    # Random Forest 參數
    rf_n_estimators: int = 100
    rf_max_depth: int = 10
    rf_min_samples_split: int = 5
    rf_min_samples_leaf: int = 2
    
    # Gradient Boosting 參數
    gb_n_estimators: int = 100
    gb_learning_rate: float = 0.1
    gb_max_depth: int = 6


@dataclass
class ModelMetrics:
    """模型評估指標"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: Optional[float]
    cv_score_mean: float
    cv_score_std: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'auc_roc': self.auc_roc,
            'cv_score_mean': self.cv_score_mean,
            'cv_score_std': self.cv_score_std
        }


class ModelTrainer:
    """
    模型訓練器
    
    支持多種機器學習模型的訓練和評估
    """
    
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.metrics: Optional[ModelMetrics] = None
        self.training_history: List[Dict[str, Any]] = []
        
    def create_model(self, model_type: Optional[str] = None) -> Any:
        """
        創建模型實例
        
        Args:
            model_type: 模型類型
            
        Returns:
            模型實例
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn未安裝，使用簡單模擬模型")
            return MockModel()
        
        model_type = model_type or self.config.model_type
        
        if model_type == "random_forest":
            model = RandomForestClassifier(
                n_estimators=self.config.rf_n_estimators,
                max_depth=self.config.rf_max_depth,
                min_samples_split=self.config.rf_min_samples_split,
                min_samples_leaf=self.config.rf_min_samples_leaf,
                random_state=self.config.random_state,
                n_jobs=-1
            )
        elif model_type == "gradient_boosting":
            model = GradientBoostingClassifier(
                n_estimators=self.config.gb_n_estimators,
                learning_rate=self.config.gb_learning_rate,
                max_depth=self.config.gb_max_depth,
                random_state=self.config.random_state
            )
        else:
            raise ValueError(f"不支持的模型類型: {model_type}")
        
        return model
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: Optional[str] = None,
        validation_split: bool = True
    ) -> Any:
        """
        訓練模型
        
        Args:
            X: 特徵數據
            y: 目標變量
            model_type: 模型類型
            validation_split: 是否分割驗證集
            
        Returns:
            訓練好的模型
        """
        logger.info(f"開始訓練模型: {model_type or self.config.model_type}")
        
        # 創建模型
        self.model = self.create_model(model_type)
        
        if validation_split and SKLEARN_AVAILABLE:
            # 分割訓練集和測試集
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=self.config.test_size,
                random_state=self.config.random_state,
                shuffle=False  # 時間序列不分亂序
            )
            
            # 訓練模型
            self.model.fit(X_train, y_train)
            
            # 評估模型
            self.metrics = self._evaluate_model(X_test, y_test)
            
            # 交叉驗證
            from sklearn.model_selection import cross_val_score
            cv_scores = cross_val_score(
                self.model, X, y,
                cv=self.config.cv_folds,
                scoring='accuracy'
            )
            
            logger.info(f"交叉驗證準確率: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
            
            # 更新指標
            self.metrics.cv_score_mean = cv_scores.mean()
            self.metrics.cv_score_std = cv_scores.std()
        else:
            # 使用全部數據訓練
            self.model.fit(X, y)
            
            # 簡單評估
            y_pred = self.model.predict(X)
            
            if SKLEARN_AVAILABLE:
                from sklearn.metrics import accuracy_score
                accuracy = accuracy_score(y, y_pred)
            else:
                accuracy = 0.5
                
            self.metrics = ModelMetrics(
                accuracy=accuracy,
                precision=0,
                recall=0,
                f1_score=0,
                auc_roc=None,
                cv_score_mean=accuracy,
                cv_score_std=0
            )
        
        logger.info(f"模型訓練完成 | 準確率: {self.metrics.accuracy:.4f}")
        
        # 記錄訓練歷史
        self.training_history.append({
            'timestamp': datetime.now().isoformat(),
            'model_type': model_type or self.config.model_type,
            'metrics': self.metrics.to_dict()
        })
        
        return self.model
    
    def _evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series) -> ModelMetrics:
        """評估模型性能"""
        y_pred = self.model.predict(X_test)
        
        # 計算各項指標
        accuracy = accuracy_score(y_test, y_pred)
        
        # 對於多分類，使用 weighted average
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        # AUC-ROC (僅適用於二分類或ovr)
        try:
            if len(np.unique(y_test)) == 2:
                y_pred_proba = self.model.predict_proba(X_test)[:, 1]
                auc_roc = roc_auc_score(y_test, y_pred_proba)
            else:
                y_pred_proba = self.model.predict_proba(X_test)
                auc_roc = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
        except Exception:
            auc_roc = None
        
        metrics = ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            auc_roc=auc_roc,
            cv_score_mean=0,
            cv_score_std=0
        )
        
        # 打印評估報告
        logger.info("\n" + "="*50)
        logger.info("模型評估報告")
        logger.info("="*50)
        logger.info(f"準確率: {accuracy:.4f}")
        logger.info(f"精確率: {precision:.4f}")
        logger.info(f"召回率: {recall:.4f}")
        logger.info(f"F1分數: {f1:.4f}")
        if auc_roc:
            logger.info(f"AUC-ROC: {auc_roc:.4f}")
        logger.info("="*50)
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        預測
        
        Args:
            X: 特徵數據
            
        Returns:
            預測結果
        """
        if self.model is None:
            raise ValueError("模型尚未訓練")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        預測概率
        
        Args:
            X: 特徵數據
            
        Returns:
            預測概率
        """
        if self.model is None:
            raise ValueError("模型尚未訓練")
        
        return self.model.predict_proba(X)
    
    def hyperparameter_search(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        param_grid: Optional[Dict[str, List]] = None
    ) -> Dict[str, Any]:
        """
        超參數搜索
        
        Args:
            X: 特徵數據
            y: 目標變量
            param_grid: 參數網格
            
        Returns:
            最佳參數
        """
        if param_grid is None:
            if self.config.model_type == "random_forest":
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 15],
                    'min_samples_split': [2, 5, 10]
                }
            else:
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.05, 0.1, 0.2],
                    'max_depth': [3, 6, 9]
                }
        
        logger.info("開始超參數搜索...")
        
        model = self.create_model()
        
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=self.config.cv_folds,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        logger.info(f"最佳參數: {grid_search.best_params_}")
        logger.info(f"最佳分數: {grid_search.best_score_:.4f}")
        
        # 更新模型為最佳模型
        self.model = grid_search.best_estimator_
        
        return {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }
    
    def get_feature_importance(self, feature_names: List[str]) -> Dict[str, float]:
        """
        獲取特徵重要性
        
        Args:
            feature_names: 特徵名稱列表
            
        Returns:
            特徵重要性字典
        """
        if self.model is None:
            raise ValueError("模型尚未訓練")
        
        if hasattr(self.model, 'feature_importances_'):
            importance = dict(zip(feature_names, self.model.feature_importances_))
            return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        return {}
    
    def save_model(self, filepath: str):
        """
        保存模型
        
        Args:
            filepath: 保存路徑
        """
        if self.model is None:
            raise ValueError("模型尚未訓練")
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'config': self.config,
                'metrics': self.metrics,
                'training_history': self.training_history
            }, f)
        
        logger.info(f"模型已保存: {filepath}")
    
    def load_model(self, filepath: str):
        """
        加載模型
        
        Args:
            filepath: 模型路徑
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.config = data['config']
        self.metrics = data['metrics']
        self.training_history = data['training_history']
        
        logger.info(f"模型已加載: {filepath}")
    
    def get_model_summary(self) -> Dict[str, Any]:
        """獲取模型摘要"""
        return {
            'model_type': self.config.model_type,
            'is_trained': self.model is not None,
            'metrics': self.metrics.to_dict() if self.metrics else None,
            'training_count': len(self.training_history)
        }


class MockModel:
    """模擬模型 (當sklearn不可用時使用)"""
    
    def fit(self, X, y):
        return self
    
    def predict(self, X):
        return np.zeros(len(X))
    
    def predict_proba(self, X):
        n_samples = len(X)
        return np.array([[0.5, 0.5]] * n_samples)


class ModelEnsemble:
    """
    模型集成
    
    組合多個模型的預測結果
    """
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.weights: Dict[str, float] = {}
    
    def add_model(self, name: str, model: Any, weight: float = 1.0):
        """添加模型"""
        self.models[name] = model
        self.weights[name] = weight
        logger.info(f"模型 '{name}' 已添加到集成 (權重: {weight})")
    
    def predict(self, X: pd.DataFrame, method: str = "weighted_vote") -> np.ndarray:
        """
        集成預測
        
        Args:
            X: 特徵數據
            method: 集成方法 (weighted_vote, average_proba)
            
        Returns:
            預測結果
        """
        if not self.models:
            raise ValueError("沒有模型可供預測")
        
        if method == "weighted_vote":
            # 加權投票
            votes = []
            for name, model in self.models.items():
                pred = model.predict(X)
                weight = self.weights.get(name, 1.0)
                votes.append(pred * weight)
            
            # 加權平均
            ensemble_pred = np.round(np.mean(votes, axis=0)).astype(int)
            return ensemble_pred
        
        elif method == "average_proba":
            # 平均概率
            probas = []
            for name, model in self.models.items():
                proba = model.predict_proba(X)
                weight = self.weights.get(name, 1.0)
                probas.append(proba * weight)
            
            avg_proba = np.mean(probas, axis=0)
            return np.argmax(avg_proba, axis=1)
        
        else:
            raise ValueError(f"不支持的集成方法: {method}")
    
    def set_weights(self, weights: Dict[str, float]):
        """設置模型權重"""
        self.weights.update(weights)


# 便捷函數
def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_type: str = "random_forest"
) -> Tuple[Any, ModelMetrics]:
    """便捷函數：訓練模型"""
    config = ModelConfig(model_type=model_type)
    trainer = ModelTrainer(config)
    model = trainer.train(X, y)
    return model, trainer.metrics


def quick_train(df: pd.DataFrame, forward_period: int = 5) -> ModelTrainer:
    """
    快速訓練
    
    Args:
        df: 價格數據
        forward_period: 前瞻週期
        
    Returns:
        ModelTrainer實例
    """
    # 準備數據
    engineer = FeatureEngineer()
    X, y = engineer.prepare_ml_dataset(df, forward_period)
    
    # 訓練模型
    trainer = ModelTrainer()
    trainer.train(X, y)
    
    return trainer
