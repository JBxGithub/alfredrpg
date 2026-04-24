export interface TQQQStrategy {
  zscore_threshold: number;
  rsi_overbought: number;
  rsi_oversold: number;
  take_profit_pct: number;
  stop_loss_pct: number;
  time_stop_days: number;
  position_pct: number;
}

export interface TrendStrategy {
  ema_fast: number;
  ema_slow: number;
  ema_signal: number;
  indicator_confluence: number;
  volume_threshold: number;
}

export interface ZScoreStrategy {
  zscore_entry: number;
  zscore_exit: number;
  exit_condition: 'mean_reversion' | 'opposite_signal' | 'both';
  lookback_period: number;
}

export interface BreakoutStrategy {
  breakout_threshold: number;
  volume_confirm: boolean;
  volume_multiplier: number;
  consolidation_period: number;
}

export interface MomentumStrategy {
  momentum_period: number;
  rsi_period: number;
  rsi_threshold: number;
  momentum_threshold: number;
}

export interface FlexibleArbitrageStrategy {
  market_state_threshold: number;
  zscore_dynamic: boolean;
  zscore_min: number;
  zscore_max: number;
  volatility_adjust: boolean;
}

export interface MTFSettings {
  enabled: boolean;
  macd_v_enabled: boolean;
  divergence_enabled: boolean;
  monthly_weight: number;
  weekly_weight: number;
  daily_weight: number;
  min_score_threshold: number;
}

export interface RiskControl {
  max_risk_per_trade: number;
  max_daily_loss: number;
  max_positions: number;
  partial_profit_enabled: boolean;
  dynamic_stoploss_enabled: boolean;
}

export type StrategyType = 'tqqq' | 'trend' | 'zscore' | 'breakout' | 'momentum' | 'flexible_arbitrage';

export interface StrategyConfig {
  strategy_type: StrategyType;
  name: string;
  description?: string;
  tqqq: TQQQStrategy;
  trend: TrendStrategy;
  zscore: ZScoreStrategy;
  breakout: BreakoutStrategy;
  momentum: MomentumStrategy;
  flexible_arbitrage: FlexibleArbitrageStrategy;
  mtf: MTFSettings;
  risk: RiskControl;
}

export interface ConfigResponse {
  success: boolean;
  message: string;
  config?: StrategyConfig;
  errors?: string[];
}

export interface StrategyInfo {
  id: StrategyType;
  name: string;
  description: string;
}
