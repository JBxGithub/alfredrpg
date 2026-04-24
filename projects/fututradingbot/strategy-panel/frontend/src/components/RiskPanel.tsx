import React from 'react';
import { SliderInput } from './SliderInput';
import { ToggleSwitch } from './ToggleSwitch';
import { RiskControl } from '../types';
import './RiskPanel.css';

interface RiskPanelProps {
  config: RiskControl;
  onChange: (config: RiskControl) => void;
}

export const RiskPanel: React.FC<RiskPanelProps> = ({ config, onChange }) => {
  const updateField = <K extends keyof RiskControl>(field: K, value: RiskControl[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="risk-panel">
      <h3 className="panel-title">風險控制設定</h3>
      <p className="panel-description">交易風險管理參數</p>
      
      <div className="panel-section">
        <h4 className="section-title">風險限制</h4>
        <SliderInput
          label="單筆最大風險"
          value={config.max_risk_per_trade}
          min={0.1}
          max={5.0}
          step={0.1}
          unit="%"
          onChange={(v) => updateField('max_risk_per_trade', v)}
        />
        <SliderInput
          label="每日最大虧損"
          value={config.max_daily_loss}
          min={0.5}
          max={10.0}
          step={0.5}
          unit="%"
          onChange={(v) => updateField('max_daily_loss', v)}
        />
        <SliderInput
          label="最大持倉數"
          value={config.max_positions}
          min={1}
          max={10}
          step={1}
          onChange={(v) => updateField('max_positions', v)}
        />
      </div>

      <div className="panel-section">
        <h4 className="section-title">進階功能</h4>
        <ToggleSwitch
          label="部分獲利"
          checked={config.partial_profit_enabled}
          onChange={(v) => updateField('partial_profit_enabled', v)}
        />
        <ToggleSwitch
          label="動態止損"
          checked={config.dynamic_stoploss_enabled}
          onChange={(v) => updateField('dynamic_stoploss_enabled', v)}
        />
      </div>

      <div className="risk-summary">
        <div className="risk-item">
          <span className="risk-label">單筆風險:</span>
          <span className="risk-value">{config.max_risk_per_trade}%</span>
        </div>
        <div className="risk-item">
          <span className="risk-label">日內風險:</span>
          <span className="risk-value">{config.max_daily_loss}%</span>
        </div>
        <div className="risk-item">
          <span className="risk-label">最大持倉:</span>
          <span className="risk-value">{config.max_positions} 筆</span>
        </div>
      </div>
    </div>
  );
};
