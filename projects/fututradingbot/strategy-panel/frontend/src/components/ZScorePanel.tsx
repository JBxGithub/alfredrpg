import React from 'react';
import { SliderInput } from './SliderInput';
import { ZScoreStrategy } from '../types';
import './StrategyPanels.css';

interface ZScorePanelProps {
  config: ZScoreStrategy;
  onChange: (config: ZScoreStrategy) => void;
}

export const ZScorePanel: React.FC<ZScorePanelProps> = ({ config, onChange }) => {
  const updateField = <K extends keyof ZScoreStrategy>(field: K, value: ZScoreStrategy[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="strategy-panel">
      <h3 className="panel-title">ZScore 策略配置</h3>
      <p className="panel-description">純Z-Score均值回歸策略</p>
      
      <div className="panel-section">
        <h4 className="section-title">Z-Score參數</h4>
        <SliderInput
          label="Z-Score入場閾值"
          value={config.zscore_entry}
          min={0.5}
          max={4.0}
          step={0.1}
          onChange={(v) => updateField('zscore_entry', v)}
        />
        <SliderInput
          label="Z-Score出場閾值"
          value={config.zscore_exit}
          min={0.1}
          max={2.0}
          step={0.1}
          onChange={(v) => updateField('zscore_exit', v)}
        />
        <SliderInput
          label="回望週期"
          value={config.lookback_period}
          min={10}
          max={60}
          step={1}
          onChange={(v) => updateField('lookback_period', v)}
        />
      </div>

      <div className="panel-section">
        <h4 className="section-title">出場條件</h4>
        <div className="select-container">
          <label className="select-label">出場條件類型</label>
          <select
            value={config.exit_condition}
            onChange={(e) => updateField('exit_condition', e.target.value as any)}
            className="select-input"
          >
            <option value="mean_reversion">均值回歸</option>
            <option value="opposite_signal">反向信號</option>
            <option value="both">兩者皆可</option>
          </select>
        </div>
      </div>
    </div>
  );
};
