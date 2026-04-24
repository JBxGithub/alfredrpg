import React from 'react';
import { SliderInput } from './SliderInput';
import { ToggleSwitch } from './ToggleSwitch';
import { MTFSettings } from '../types';
import './MTFPanel.css';

interface MTFPanelProps {
  config: MTFSettings;
  onChange: (config: MTFSettings) => void;
}

export const MTFPanel: React.FC<MTFPanelProps> = ({ config, onChange }) => {
  const updateField = <K extends keyof MTFSettings>(field: K, value: MTFSettings[K]) => {
    onChange({ ...config, [field]: value });
  };

  const totalWeight = config.monthly_weight + config.weekly_weight + config.daily_weight;
  const isValidWeight = totalWeight === 100;

  return (
    <div className="mtf-panel">
      <h3 className="panel-title">MTF 多時間框架設定</h3>
      <p className="panel-description">多時間框架分析配置</p>
      
      <div className="panel-section">
        <h4 className="section-title">功能開關</h4>
        <ToggleSwitch
          label="MTF分析"
          checked={config.enabled}
          onChange={(v) => updateField('enabled', v)}
        />
        <ToggleSwitch
          label="MACD-V"
          checked={config.macd_v_enabled}
          onChange={(v) => updateField('macd_v_enabled', v)}
        />
        <ToggleSwitch
          label="背離檢測"
          checked={config.divergence_enabled}
          onChange={(v) => updateField('divergence_enabled', v)}
        />
      </div>

      <div className="panel-section">
        <h4 className="section-title">時間框架權重</h4>
        {!isValidWeight && (
          <div className="weight-warning">
            ⚠️ 權重總和必須為100%，當前為{totalWeight}%
          </div>
        )}
        <SliderInput
          label="月線權重"
          value={config.monthly_weight}
          min={0}
          max={100}
          step={5}
          unit="%"
          onChange={(v) => updateField('monthly_weight', v)}
        />
        <SliderInput
          label="週線權重"
          value={config.weekly_weight}
          min={0}
          max={100}
          step={5}
          unit="%"
          onChange={(v) => updateField('weekly_weight', v)}
        />
        <SliderInput
          label="日線權重"
          value={config.daily_weight}
          min={0}
          max={100}
          step={5}
          unit="%"
          onChange={(v) => updateField('daily_weight', v)}
        />
        <div className={`weight-total ${isValidWeight ? 'valid' : 'invalid'}`}>
          總權重: {totalWeight}%
        </div>
      </div>

      <div className="panel-section">
        <h4 className="section-title">評分設定</h4>
        <SliderInput
          label="最低評分閾值"
          value={config.min_score_threshold}
          min={0}
          max={100}
          step={5}
          unit="分"
          onChange={(v) => updateField('min_score_threshold', v)}
        />
      </div>
    </div>
  );
};
