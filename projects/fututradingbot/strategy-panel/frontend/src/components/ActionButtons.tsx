import React, { useState } from 'react';
import { StrategyConfig, ConfigResponse } from '../types';
import { configApi } from '../utils/api';
import './ActionButtons.css';

interface ActionButtonsProps {
  config: StrategyConfig;
  onConfigChange: (config: StrategyConfig) => void;
  onSaveSuccess: (message: string) => void;
  onError: (message: string) => void;
}

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  config,
  onConfigChange,
  onSaveSuccess,
  onError,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importJson, setImportJson] = useState('');
  const [saveName, setSaveName] = useState('');
  const [showSaveModal, setShowSaveModal] = useState(false);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const response: ConfigResponse = await configApi.updateConfig(config);
      if (response.success) {
        onSaveSuccess('配置已保存到系統');
      } else {
        onError(response.errors?.join(', ') || '保存失敗');
      }
    } catch (error) {
      onError('保存配置時發生錯誤');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('確定要重置為默認配置嗎？')) return;
    setIsLoading(true);
    try {
      const response = await configApi.resetConfig();
      if (response.success && response.config) {
        onConfigChange(response.config);
        onSaveSuccess('配置已重置為默認值');
      }
    } catch (error) {
      onError('重置配置時發生錯誤');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApply = async () => {
    setIsLoading(true);
    try {
      const response = await configApi.applyConfig();
      if (response.success) {
        onSaveSuccess('配置已應用到交易系統');
      }
    } catch (error) {
      onError('應用配置時發生錯誤');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await configApi.exportConfig();
      if (response.success) {
        const blob = new Blob([response.config_json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `strategy-config-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        onSaveSuccess('配置已導出');
      }
    } catch (error) {
      onError('導出配置時發生錯誤');
    }
  };

  const handleImport = async () => {
    try {
      const response = await configApi.importConfig(importJson);
      if (response.success && response.config) {
        onConfigChange(response.config);
        setShowImportModal(false);
        setImportJson('');
        onSaveSuccess('配置已導入');
      } else {
        onError(response.errors?.join(', ') || '導入失敗');
      }
    } catch (error) {
      onError('導入配置時發生錯誤');
    }
  };

  const handleSaveToFile = async () => {
    if (!saveName.trim()) {
      onError('請輸入配置文件名');
      return;
    }
    try {
      const response = await configApi.saveConfig(saveName);
      if (response.success) {
        setShowSaveModal(false);
        setSaveName('');
        onSaveSuccess(`配置已保存為 ${saveName}`);
      }
    } catch (error) {
      onError('保存配置文件時發生錯誤');
    }
  };

  return (
    <>
      <div className="action-buttons">
        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={isLoading}
        >
          {isLoading ? '保存中...' : '💾 保存'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleReset}
          disabled={isLoading}
        >
          🔄 重置
        </button>
        <button
          className="btn btn-success"
          onClick={handleApply}
          disabled={isLoading}
        >
          ✅ 套用
        </button>
        <button
          className="btn btn-info"
          onClick={handleExport}
          disabled={isLoading}
        >
          📤 導出
        </button>
        <button
          className="btn btn-warning"
          onClick={() => setShowImportModal(true)}
          disabled={isLoading}
        >
          📥 導入
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => setShowSaveModal(true)}
          disabled={isLoading}
        >
          💾 另存為
        </button>
      </div>

      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>導入配置</h3>
            <textarea
              value={importJson}
              onChange={(e) => setImportJson(e.target.value)}
              placeholder="在此貼上JSON配置..."
              rows={10}
              className="import-textarea"
            />
            <div className="modal-buttons">
              <button className="btn btn-secondary" onClick={() => setShowImportModal(false)}>
                取消
              </button>
              <button className="btn btn-primary" onClick={handleImport}>
                導入
              </button>
            </div>
          </div>
        </div>
      )}

      {showSaveModal && (
        <div className="modal-overlay" onClick={() => setShowSaveModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>保存配置</h3>
            <input
              type="text"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              placeholder="輸入配置文件名..."
              className="save-input"
            />
            <div className="modal-buttons">
              <button className="btn btn-secondary" onClick={() => setShowSaveModal(false)}>
                取消
              </button>
              <button className="btn btn-primary" onClick={handleSaveToFile}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
