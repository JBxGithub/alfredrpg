"""
風險檢查器 - Risk Checker

自動檢查交易風險，確保安全
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.utils.logger import logger

# 簡化 logger 避免依賴問題
try:
    from src.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskCheck:
    """風險檢查項"""
    name: str
    level: RiskLevel
    passed: bool
    message: str
    value: Any = None
    threshold: Any = None


class RiskChecker:
    """
    風險檢查器
    
    檢查項目：
    - 資金充足性
    - 倉位限制
    - 日虧損限制
    - 最大回撤
    - API 連接狀態
    """
    
    def __init__(self):
        self.checks: List[RiskCheck] = []
        self.last_check_time: Optional[datetime] = None
        self.is_trading_allowed = False
    
    async def full_check(self, context: Dict[str, Any]) -> bool:
        """
        執行完整風險檢查
        
        Args:
            context: 當前交易上下文
            
        Returns:
            bool: 是否通過所有檢查
        """
        logger.info("🔍 執行完整風險檢查...")
        self.checks = []
        
        # 檢查 1: 資金充足
        self._check_capital(context)
        
        # 檢查 2: 日虧損限制
        self._check_daily_loss(context)
        
        # 檢查 3: 最大回撤
        self._check_drawdown(context)
        
        # 檢查 4: 倉位數量
        self._check_position_count(context)
        
        # 檢查 5: API 連接
        await self._check_api_connection(context)
        
        self.last_check_time = datetime.now()
        
        # 評估結果
        critical_failed = any(
            c.level == RiskLevel.CRITICAL and not c.passed 
            for c in self.checks
        )
        high_failed = sum(
            1 for c in self.checks 
            if c.level == RiskLevel.HIGH and not c.passed
        ) >= 2
        
        self.is_trading_allowed = not critical_failed and not high_failed
        
        if self.is_trading_allowed:
            logger.info("✅ 風險檢查通過，允許交易")
        else:
            logger.error("❌ 風險檢查未通過，禁止交易")
            for check in self.checks:
                if not check.passed:
                    logger.warning(f"  - {check.name}: {check.message}")
        
        return self.is_trading_allowed
    
    def _check_capital(self, context: Dict[str, Any]):
        """檢查資金"""
        capital = context.get('available_capital', 0)
        min_capital = context.get('min_capital_required', 10000)
        
        passed = capital >= min_capital
        self.checks.append(RiskCheck(
            name="資金充足性",
            level=RiskLevel.CRITICAL,
            passed=passed,
            message=f"可用資金: ${capital:,.2f}" if passed else f"資金不足: ${capital:,.2f} < ${min_capital:,.2f}",
            value=capital,
            threshold=min_capital
        ))
    
    def _check_daily_loss(self, context: Dict[str, Any]):
        """檢查日虧損"""
        daily_pnl = context.get('daily_pnl_pct', 0)
        max_daily_loss = context.get('max_daily_loss_pct', 0.05)
        
        passed = daily_pnl > -max_daily_loss
        level = RiskLevel.CRITICAL if daily_pnl < -max_daily_loss * 1.5 else RiskLevel.HIGH
        
        self.checks.append(RiskCheck(
            name="日虧損限制",
            level=level,
            passed=passed,
            message=f"日盈虧: {daily_pnl:.2%}" if passed else f"日虧損超標: {daily_pnl:.2%}",
            value=daily_pnl,
            threshold=-max_daily_loss
        ))
    
    def _check_drawdown(self, context: Dict[str, Any]):
        """檢查回撤"""
        drawdown = context.get('current_drawdown', 0)
        max_drawdown = context.get('max_allowed_drawdown', 0.10)
        
        passed = drawdown < max_drawdown
        level = RiskLevel.CRITICAL if drawdown > max_drawdown * 1.2 else RiskLevel.HIGH
        
        self.checks.append(RiskCheck(
            name="最大回撤",
            level=level,
            passed=passed,
            message=f"當前回撤: {drawdown:.2%}" if passed else f"回撤超標: {drawdown:.2%}",
            value=drawdown,
            threshold=max_drawdown
        ))
    
    def _check_position_count(self, context: Dict[str, Any]):
        """檢查倉位數量"""
        positions = context.get('open_positions', 0)
        max_positions = context.get('max_positions', 5)
        
        passed = positions < max_positions
        
        self.checks.append(RiskCheck(
            name="倉位數量",
            level=RiskLevel.MEDIUM,
            passed=passed,
            message=f"持倉: {positions}/{max_positions}",
            value=positions,
            threshold=max_positions
        ))
    
    async def _check_api_connection(self, context: Dict[str, Any]):
        """檢查 API 連接"""
        # TODO: 實際 API 檢查
        is_connected = context.get('api_connected', True)
        
        self.checks.append(RiskCheck(
            name="API 連接",
            level=RiskLevel.CRITICAL,
            passed=is_connected,
            message="API 連接正常" if is_connected else "API 連接斷開",
            value=is_connected,
            threshold=True
        ))
    
    def get_check_summary(self) -> Dict[str, Any]:
        """獲取檢查摘要"""
        return {
            'total_checks': len(self.checks),
            'passed': sum(1 for c in self.checks if c.passed),
            'failed': sum(1 for c in self.checks if not c.passed),
            'is_trading_allowed': self.is_trading_allowed,
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
            'details': [
                {
                    'name': c.name,
                    'level': c.level.value,
                    'passed': c.passed,
                    'message': c.message
                }
                for c in self.checks
            ]
        }
