import axios from 'axios';
import type {
  ChainListResponse,
  ProtocolListResponse,
  TVLHistoryListResponse,
  YieldListResponse,
  TopYieldResponse,
} from '../types';

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_BASE_URL || ''}/api/v1`,
  timeout: 30000,
});

export const chainsApi = {
  list: async (params: {
    page?: number;
    page_size?: number;
    sort_by?: string;
    order?: string;
  }) => {
    const { data } = await api.get<ChainListResponse>('/chains', { params });
    return data;
  },
  get: async (chainId: string) => {
    const { data } = await api.get(`/chains/${chainId}`);
    return data;
  },
};

export const protocolsApi = {
  list: async (params: {
    page?: number;
    page_size?: number;
    sort_by?: string;
    order?: string;
    category?: string;
    chain?: string;
  }) => {
    const { data } = await api.get<ProtocolListResponse>('/protocols', { params });
    return data;
  },
  get: async (protocolId: string) => {
    const { data } = await api.get(`/protocols/${protocolId}`);
    return data;
  },
};

export const tvlApi = {
  history: async (params: {
    entity_type?: string;
    entity_id?: string;
    chain_id?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }) => {
    const { data } = await api.get<TVLHistoryListResponse>('/tvl/history', { params });
    return data;
  },
};

export const yieldsApi = {
  list: async (params: {
    page?: number;
    page_size?: number;
    chain?: string;
    min_tvl?: number;
  }) => {
    const { data } = await api.get<YieldListResponse>('/yields', { params });
    return data;
  },
  top: async (params: {
    page?: number;
    page_size?: number;
    min_tvl?: number;
    sort_by?: string;
  }) => {
    const { data } = await api.get<TopYieldResponse>('/yields/top', { params });
    return data;
  },
};

export default api;
