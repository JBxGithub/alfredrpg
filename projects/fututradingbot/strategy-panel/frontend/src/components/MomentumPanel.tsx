import React from 'react';
import { SliderInput } from './SliderInput';
import { MomentumStrategy } from '../types';
import './StrategyPanels.css';

interface MomentumPanelProps {
  config: MomentumStrategy;
  onChange: (config: MomentumStrategy) => void;
}

export const MomentumPanel: React.FC<MomentumPanelProps> = ({ config, onChange }) => {
  const updateField = <K extends keyof MomentumStrategy>(field: K, value: MomentumStrategy[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="strategy-panel">
      <h3 className="panel-title">Momentum 策略配置</h3>
      <p className="panel-description">動量交易策略</p>
      
      <div className="panel-section">
        <h4 className="section-title">動量參數</h4>
        <SliderInput
          label="動量週期"
          value={config.momentum_period}
          min={5}
          max={30}
          step={1}
          onChange={(v) => updateField('momentum_period', v)}
        />
        <SliderInput
          label="動量閾值"
          value={config.momentum_threshold}
          min={-10}
          max={10}
          step={0.5}
          onChange={(v) => updateField('momentum_threshold', v)}
        />
      </div>

      <div className="panel-section">
        <h4 className="section-title">RSI參數</h4>
        <SliderInput
          label="RSI週期"
          value={config.rsi_period}
          min={5}
          max={30}
          step={1}
          onChange={(v) => updateField('rsi_period', v)}
        />
        <SliderInput
          label="RSI閾值"
          value={config.rsi_threshold}
          min={30}
          max={70}
          step={1}
          onChange={(v) => updateField('rsi_threshold', v)}
        />
      </div>
    </div>
  );
};
