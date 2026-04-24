from typing import Dict, Any, Optional
import json
import os
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "saved_configs"
CONFIG_DIR.mkdir(exist_ok=True)

DEFAULT_CONFIG = {
    "strategy_type": "tqqq",
    "name": "Default Strategy",
    "description": "Default TQQQ trading strategy configuration",
    "tqqq": {
        "zscore_threshold": 1.65,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "take_profit_pct": 5.0,
        "stop_loss_pct": 3.0,
        "time_stop_days": 7,
        "position_pct": 50.0
    },
    "trend": {
        "ema_fast": 12,
        "ema_slow": 26,
        "ema_signal": 9,
        "indicator_confluence": 2,
        "volume_threshold": 1.5
    },
    "zscore": {
        "zscore_entry": 2.0,
        "zscore_exit": 0.5,
        "exit_condition": "mean_reversion",
        "lookback_period": 20
    },
    "breakout": {
        "breakout_threshold": 2.0,
        "volume_confirm": True,
        "volume_multiplier": 2.0,
        "consolidation_period": 20
    },
    "momentum": {
        "momentum_period": 14,
        "rsi_period": 14,
        "rsi_threshold": 50,
        "momentum_threshold": 0.0
    },
    "flexible_arbitrage": {
        "market_state_threshold": 0.5,
        "zscore_dynamic": True,
        "zscore_min": 1.5,
        "zscore_max": 2.5,
        "volatility_adjust": True
    },
    "mtf": {
        "enabled": True,
        "macd_v_enabled": True,
        "divergence_enabled": True,
        "monthly_weight": 40,
        "weekly_weight": 35,
        "daily_weight": 25,
        "min_score_threshold": 60
    },
    "risk": {
        "max_risk_per_trade": 1.0,
        "max_daily_loss": 2.0,
        "max_positions": 3,
        "partial_profit_enabled": True,
        "dynamic_stoploss_enabled": True
    }
}

class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_default_config()
        return cls._instance

    def _load_default_config(self):
        self._config = DEFAULT_CONFIG.copy()

    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()

    def update_config(self, config: Dict[str, Any]) -> bool:
        try:
            self._config.update(config)
            return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False

    def reset_config(self):
        self._config = DEFAULT_CONFIG.copy()
        return self._config

    def save_to_file(self, filename: str) -> bool:
        try:
            filepath = CONFIG_DIR / f"{filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def load_from_file(self, filename: str) -> Optional[Dict[str, Any]]:
        try:
            filepath = CONFIG_DIR / f"{filename}.json"
            if not filepath.exists():
                return None
            with open(filepath, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            return self._config
        except Exception as e:
            print(f"Error loading config: {e}")
            return None

    def list_saved_configs(self) -> list:
        try:
            configs = []
            for f in CONFIG_DIR.glob("*.json"):
                configs.append(f.stem)
            return configs
        except Exception as e:
            print(f"Error listing configs: {e}")
            return []

    def export_config(self) -> str:
        return json.dumps(self._config, indent=2, ensure_ascii=False)

    def import_config(self, json_str: str) -> bool:
        try:
            imported = json.loads(json_str)
            self._config.update(imported)
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False

    def validate_weights(self) -> tuple[bool, str]:
        mtf = self._config.get("mtf", {})
        total_weight = (
            mtf.get("monthly_weight", 0) +
            mtf.get("weekly_weight", 0) +
            mtf.get("daily_weight", 0)
        )
        if total_weight != 100:
            return False, f"時間框架權重總和必須為100，當前為{total_weight}"
        return True, "驗證通過"

config_manager = ConfigManager()
