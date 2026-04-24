import React from 'react';
import { SliderInput } from './SliderInput';
import { ToggleSwitch } from './ToggleSwitch';
import { BreakoutStrategy } from '../types';
import './StrategyPanels.css';

interface BreakoutPanelProps {
  config: BreakoutStrategy;
  onChange: (config: BreakoutStrategy) => void;
}

export const BreakoutPanel: React.FC<BreakoutPanelProps> = ({ config, onChange }) => {
  const updateField = <K extends keyof BreakoutStrategy>(field: K, value: BreakoutStrategy[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="strategy-panel">
      <h3 className="panel-title">Breakout 策略配置</h3>
      <p className="panel-description">突破交易策略</p>
      
      <div className="panel-section">
        <h4 className="section-title">突破參數</h4>
        <SliderInput
          label="突破閾值"
          value={config.breakout_threshold}
          min={0.5}
          max={5.0}
          step={0.1}
          unit="%"
          onChange={(v) => updateField('breakout_threshold', v)}
        />
        <SliderInput
          label="盤整週期"
          value={config.consolidation_period}
          min={5}
          max={60}
          step={1}
          onChange={(v) => updateField('consolidation_period', v)}
        />
      </div>

      <div className="panel-section">
        <h4 className="section-title">成交量確認</h4>
        <ToggleSwitch
          label="啟用成交量確認"
          checked={config.volume_confirm}
          onChange={(v) => updateField('volume_confirm', v)}
        />
        {config.volume_confirm && (
          <SliderInput
            label="成交量倍數"
            value={config.volume_multiplier}
            min={1}
            max={5}
            step={0.1}
            unit="x"
            onChange={(v) => updateField('volume_multiplier', v)}
          />
        )}
      </div>
    </div>
  );
};
