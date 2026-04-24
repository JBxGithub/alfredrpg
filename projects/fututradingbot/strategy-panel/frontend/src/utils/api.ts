import axios from 'axios';
import { StrategyConfig, ConfigResponse, StrategyInfo } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const configApi = {
  getConfig: async (): Promise<StrategyConfig> => {
    const response = await api.get('/config');
    return response.data;
  },

  updateConfig: async (config: StrategyConfig): Promise<ConfigResponse> => {
    const response = await api.post('/config', config);
    return response.data;
  },

  resetConfig: async (): Promise<ConfigResponse> => {
    const response = await api.post('/config/reset');
    return response.data;
  },

  saveConfig: async (filename: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post(`/config/save/${filename}`);
    return response.data;
  },

  loadConfig: async (filename: string): Promise<ConfigResponse> => {
    const response = await api.post(`/config/load/${filename}`);
    return response.data;
  },

  listConfigs: async (): Promise<{ configs: string[] }> => {
    const response = await api.get('/config/list');
    return response.data;
  },

  exportConfig: async (): Promise<{ success: boolean; config_json: string }> => {
    const response = await api.post('/config/export');
    return response.data;
  },

  importConfig: async (configJson: string): Promise<ConfigResponse> => {
    const response = await api.post('/config/import', { config_json: configJson });
    return response.data;
  },

  applyConfig: async (): Promise<{ success: boolean; message: string; applied_config: StrategyConfig }> => {
    const response = await api.post('/config/apply');
    return response.data;
  },

  getStrategies: async (): Promise<{ strategies: StrategyInfo[] }> => {
    const response = await api.get('/strategies');
    return response.data;
  },

  validateConfig: async (): Promise<{ valid: boolean; message: string }> => {
    const response = await api.get('/validate');
    return response.data;
  },
};
