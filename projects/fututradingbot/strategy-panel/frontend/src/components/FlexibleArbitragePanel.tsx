import React from 'react';
import { SliderInput } from './SliderInput';
import { ToggleSwitch } from './ToggleSwitch';
import { FlexibleArbitrageStrategy } from '../types';
import './StrategyPanels.css';

interface FlexibleArbitragePanelProps {
  config: FlexibleArbitrageStrategy;
  onChange: (config: FlexibleArbitrageStrategy) => void;
}

export const FlexibleArbitragePanel: React.FC<FlexibleArbitragePanelProps> = ({ config, onChange }) => {
  const updateField = <K extends keyof FlexibleArbitrageStrategy>(field: K, value: FlexibleArbitrageStrategy[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="strategy-panel">
      <h3 className="panel-title">Flexible Arbitrage 策略配置</h3>
      <p className="panel-description">靈活套利策略</p>
      
      <div className="panel-section">
        <h4 className="section-title">市場狀態</h4>
        <SliderInput
          label="市場狀態閾值"
          value={config.market_state_threshold}
          min={0.1}
          max={1.0}
          step={0.05}
          onChange={(v) => updateField('market_state_threshold', v)}
        />
        <ToggleSwitch
          label="波動率調整"
          checked={config.volatility_adjust}
          onChange={(v) => updateField('volatility_adjust', v)}
        />
      </div>

      <div className="panel-section">
        <h4 className="section-title">Z-Score動態調整</h4>
        <ToggleSwitch
          label="啟用Z-Score動態調整"
          checked={config.zscore_dynamic}
          onChange={(v) => updateField('zscore_dynamic', v)}
        />
        {config.zscore_dynamic && (
          <>
            <SliderInput
              label="Z-Score最小值"
              value={config.zscore_min}
              min={0.5}
              max={3.0}
              step={0.1}
              onChange={(v) => updateField('zscore_min', v)}
            />
            <SliderInput
              label="Z-Score最大值"
              value={config.zscore_max}
              min={1.5}
              max={4.0}
              step={0.1}
              onChange={(v) => updateField('zscore_max', v)}
            />
          </>
        )}
      </div>
    </div>
  );
};
