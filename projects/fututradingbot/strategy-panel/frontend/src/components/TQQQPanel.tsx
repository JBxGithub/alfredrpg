import React from 'react';
import { SliderInput } from './SliderInput';
import { TQQQStrategy } from '../types';
import './StrategyPanels.css';

interface TQQQPanelProps {
  config: TQQQStrategy;
  onChange: (config: TQQQStrategy) => void;
}

export const TQQQPanel: React.FC<TQQQPanelProps> = ({ config, onChange }) => {
  const updateField = <K extends keyof TQQQStrategy>(field: K, value: TQQQStrategy[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="strategy-panel">
      <h3 className="panel-title">TQQQ 策略配置</h3>
      <p className="panel-description">基於Z-Score和RSI的均值回歸策略</p>
      
      <div className="panel-section">
        <h4 className="section-title">入場條件</h4>
        <SliderInput
          label="Z-Score閾值"
          value={config.zscore_threshold}
          min={0.5}
          max={3.0}
          step={0.05}
          onChange={(v) => updateField('zscore_threshold', v)}
        />
        <SliderInput
          label="RSI超買閾值"
          value={config.rsi_overbought}
          min={50}
          max={90}
          step={1}
          onChange={(v) => updateField('rsi_overbought', v)}
        />
        <SliderInput
          label="RSI超賣閾值"
          value={config.rsi_oversold}
          min={10}
          max={50}
          step={1}
          onChange={(v) => updateField('rsi_oversold', v)}
        />
      </div>

      <div className="panel-section">
        <h4 className="section-title">出場條件</h4>
        <SliderInput
          label="止盈百分比"
          value={config.take_profit_pct}
          min={1}
          max={20}
          step={0.5}
          unit="%"
          onChange={(v) => updateField('take_profit_pct', v)}
        />
        <SliderInput
          label="止損百分比"
          value={config.stop_loss_pct}
          min={0.5}
          max={10}
          step={0.5}
          unit="%"
          onChange={(v) => updateField('stop_loss_pct', v)}
        />
        <SliderInput
          label="時間止損天數"
          value={config.time_stop_days}
          min={1}
          max={30}
          step={1}
          unit="天"
          onChange={(v) => updateField('time_stop_days', v)}
        />
      </div>

      <div className="panel-section">
        <h4 className="section-title">倉位管理</h4>
        <SliderInput
          label="倉位百分比"
          value={config.position_pct}
          min={10}
          max={100}
          step={5}
          unit="%"
          onChange={(v) => updateField('position_pct', v)}
        />
      </div>
    </div>
  );
};
