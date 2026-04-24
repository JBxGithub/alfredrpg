import React from 'react';
import { SliderInput } from './SliderInput';
import { TrendStrategy } from '../types';
import './StrategyPanels.css';

interface TrendPanelProps {
  config: TrendStrategy;
  onChange: (config: TrendStrategy) => void;
}

export const TrendPanel: React.FC<TrendPanelProps> = ({ config, onChange }) => {
  const updateField = <K extends keyof TrendStrategy>(field: K, value: TrendStrategy[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="strategy-panel">
      <h3 className="panel-title">Trend 策略配置</h3>
      <p className="panel-description">基於EMA和指標共振的趨勢跟踪策略</p>
      
      <div className="panel-section">
        <h4 className="section-title">EMA參數</h4>
        <SliderInput
          label="EMA快線週期"
          value={config.ema_fast}
          min={5}
          max={50}
          step={1}
          onChange={(v) => updateField('ema_fast', v)}
        />
        <SliderInput
          label="EMA慢線週期"
          value={config.ema_slow}
          min={20}
          max={100}
          step={1}
          onChange={(v) => updateField('ema_slow', v)}
        />
        <SliderInput
          label="EMA信號週期"
          value={config.ema_signal}
          min={5}
          max={20}
          step={1}
          onChange={(v) => updateField('ema_signal', v)}
        />
      </div>

      <div className="panel-section">
        <h4 className="section-title">過濾條件</h4>
        <SliderInput
          label="指標共振數量"
          value={config.indicator_confluence}
          min={1}
          max={5}
          step={1}
          onChange={(v) => updateField('indicator_confluence', v)}
        />
        <SliderInput
          label="成交量閾值倍數"
          value={config.volume_threshold}
          min={1}
          max={5}
          step={0.1}
          unit="x"
          onChange={(v) => updateField('volume_threshold', v)}
        />
      </div>
    </div>
  );
};
