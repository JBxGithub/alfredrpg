import React, { useState, useEffect } from 'react';
import { StrategyConfig, StrategyType, StrategyInfo } from '../types';
import { configApi } from '../utils/api';
import { TQQQPanel } from '../components/TQQQPanel';
import { TrendPanel } from '../components/TrendPanel';
import { ZScorePanel } from '../components/ZScorePanel';
import { BreakoutPanel } from '../components/BreakoutPanel';
import { MomentumPanel } from '../components/MomentumPanel';
import { FlexibleArbitragePanel } from '../components/FlexibleArbitragePanel';
import { MTFPanel } from '../components/MTFPanel';
import { RiskPanel } from '../components/RiskPanel';
import { ActionButtons } from '../components/ActionButtons';
import './ConfigPage.css';

const defaultConfig: StrategyConfig = {
  strategy_type: 'tqqq',
  name: 'Default Strategy',
  description: '',
  tqqq: {
    zscore_threshold: 1.65,
    rsi_overbought: 70,
    rsi_oversold: 30,
    take_profit_pct: 5.0,
    stop_loss_pct: 3.0,
    time_stop_days: 7,
    position_pct: 50.0,
  },
  trend: {
    ema_fast: 12,
    ema_slow: 26,
    ema_signal: 9,
    indicator_confluence: 2,
    volume_threshold: 1.5,
  },
  zscore: {
    zscore_entry: 2.0,
    zscore_exit: 0.5,
    exit_condition: 'mean_reversion',
    lookback_period: 20,
  },
  breakout: {
    breakout_threshold: 2.0,
    volume_confirm: true,
    volume_multiplier: 2.0,
    consolidation_period: 20,
  },
  momentum: {
    momentum_period: 14,
    rsi_period: 14,
    rsi_threshold: 50,
    momentum_threshold: 0.0,
  },
  flexible_arbitrage: {
    market_state_threshold: 0.5,
    zscore_dynamic: true,
    zscore_min: 1.5,
    zscore_max: 2.5,
    volatility_adjust: true,
  },
  mtf: {
    enabled: true,
    macd_v_enabled: true,
    divergence_enabled: true,
    monthly_weight: 40,
    weekly_weight: 35,
    daily_weight: 25,
    min_score_threshold: 60,
  },
  risk: {
    max_risk_per_trade: 1.0,
    max_daily_loss: 2.0,
    max_positions: 3,
    partial_profit_enabled: true,
    dynamic_stoploss_enabled: true,
  },
};

export const ConfigPage: React.FC = () => {
  const [config, setConfig] = useState<StrategyConfig>(defaultConfig);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [activeTab, setActiveTab] = useState<StrategyType | 'mtf' | 'risk'>('tqqq');
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [configData, strategiesData] = await Promise.all([
        configApi.getConfig(),
        configApi.getStrategies(),
      ]);
      setConfig(configData);
      setStrategies(strategiesData.strategies);
    } catch (error) {
      showNotification('error', '無法加載配置數據');
    } finally {
      setIsLoading(false);
    }
  };

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const updateConfig = (updates: Partial<StrategyConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  };

  const renderStrategyPanel = () => {
    switch (activeTab) {
      case 'tqqq':
        return (
          <TQQQPanel
            config={config.tqqq}
            onChange={(tqqq) => updateConfig({ tqqq })}
          />
        );
      case 'trend':
        return (
          <TrendPanel
            config={config.trend}
            onChange={(trend) => updateConfig({ trend })}
          />
        );
      case 'zscore':
        return (
          <ZScorePanel
            config={config.zscore}
            onChange={(zscore) => updateConfig({ zscore })}
          />
        );
      case 'breakout':
        return (
          <BreakoutPanel
            config={config.breakout}
            onChange={(breakout) => updateConfig({ breakout })}
          />
        );
      case 'momentum':
        return (
          <MomentumPanel
            config={config.momentum}
            onChange={(momentum) => updateConfig({ momentum })}
          />
        );
      case 'flexible_arbitrage':
        return (
          <FlexibleArbitragePanel
            config={config.flexible_arbitrage}
            onChange={(flexible_arbitrage) => updateConfig({ flexible_arbitrage })}
          />
        );
      case 'mtf':
        return (
          <MTFPanel
            config={config.mtf}
            onChange={(mtf) => updateConfig({ mtf })}
          />
        );
      case 'risk':
        return (
          <RiskPanel
            config={config.risk}
            onChange={(risk) => updateConfig({ risk })}
          />
        );
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>加載中...</p>
      </div>
    );
  }

  return (
    <div className="config-page">
      <header className="page-header">
        <h1>FutuTradingBot 策略配置面板</h1>
        <p className="subtitle">專業級交易策略參數調整系統</p>
      </header>

      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}

      <ActionButtons
        config={config}
        onConfigChange={setConfig}
        onSaveSuccess={(msg) => showNotification('success', msg)}
        onError={(msg) => showNotification('error', msg)}
      />

      <div className="config-container">
        <div className="tabs-container">
          <div className="tabs-header">
            <h3>策略選擇</h3>
          </div>
          <div className="tabs">
            {strategies.map((strategy) => (
              <button
                key={strategy.id}
                className={`tab ${activeTab === strategy.id ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(strategy.id);
                  updateConfig({ strategy_type: strategy.id });
                }}
              >
                {strategy.name}
              </button>
            ))}
            <div className="tab-divider"></div>
            <button
              className={`tab ${activeTab === 'mtf' ? 'active' : ''}`}
              onClick={() => setActiveTab('mtf')}
            >
              MTF設定
            </button>
            <button
              className={`tab ${activeTab === 'risk' ? 'active' : ''}`}
              onClick={() => setActiveTab('risk')}
            >
              風險控制
            </button>
          </div>
        </div>

        <div className="panel-container">
          {renderStrategyPanel()}
        </div>
      </div>
    </div>
  );
};
