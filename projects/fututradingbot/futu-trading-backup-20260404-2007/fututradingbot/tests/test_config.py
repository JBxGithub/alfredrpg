"""
測試配置加載
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings


def test_settings():
    """測試配置加載"""
    settings = Settings()
    
    print("配置測試結果:")
    print(f"OpenD Host: {settings.opend.host}")
    print(f"OpenD Port: {settings.opend.port}")
    print(f"Trading Env: {settings.trading.env}")
    print(f"Markets: {settings.trading.markets}")
    print(f"Log Level: {settings.logging.level}")
    print(f"Max Position Ratio: {settings.risk.max_position_ratio}")
    
    print("\n完整配置:")
    import json
    print(json.dumps(settings.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    test_settings()
