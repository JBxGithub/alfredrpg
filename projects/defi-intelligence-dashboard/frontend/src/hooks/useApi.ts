import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { chainsApi, protocolsApi, tvlApi, yieldsApi } from '../services/api';
import type {
  ChainListResponse,
  ProtocolListResponse,
  TVLHistoryListResponse,
  YieldListResponse,
  TopYieldResponse,
} from '../types';

const REFETCH_INTERVAL = 60000;

export function useChains(params: {
  page?: number;
  page_size?: number;
  sort_by?: string;
  order?: string;
}): UseQueryResult<ChainListResponse> {
  return useQuery({
    queryKey: ['chains', params],
    queryFn: () => chainsApi.list(params),
    refetchInterval: REFETCH_INTERVAL,
    staleTime: 30000,
  });
}

export function useProtocols(params: {
  page?: number;
  page_size?: number;
  sort_by?: string;
  order?: string;
  category?: string;
  chain?: string;
}): UseQueryResult<ProtocolListResponse> {
  return useQuery({
    queryKey: ['protocols', params],
    queryFn: () => protocolsApi.list(params),
    refetchInterval: REFETCH_INTERVAL,
    staleTime: 30000,
  });
}

export function useTVLHistory(params: {
  entity_type?: string;
  entity_id?: string;
  chain_id?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}): UseQueryResult<TVLHistoryListResponse> {
  return useQuery({
    queryKey: ['tvl-history', params],
    queryFn: () => tvlApi.history(params),
    refetchInterval: REFETCH_INTERVAL * 2,
    staleTime: 60000,
  });
}

export function useYields(params: {
  page?: number;
  page_size?: number;
  chain?: string;
  min_tvl?: number;
}): UseQueryResult<YieldListResponse> {
  return useQuery({
    queryKey: ['yields', params],
    queryFn: () => yieldsApi.list(params),
    refetchInterval: REFETCH_INTERVAL,
    staleTime: 30000,
  });
}

export function useTopYields(params: {
  page?: number;
  page_size?: number;
  min_tvl?: number;
  sort_by?: string;
}): UseQueryResult<TopYieldResponse> {
  return useQuery({
    queryKey: ['top-yields', params],
    queryFn: () => yieldsApi.top(params),
    refetchInterval: REFETCH_INTERVAL,
    staleTime: 30000,
  });
}

export function useDashboardStats() {
  const chainsQuery = useChains({ page: 1, page_size: 1 });
  const protocolsQuery = useProtocols({ page: 1, page_size: 1 });

  return {
    totalChains: chainsQuery.data?.meta.total ?? 0,
    totalProtocols: protocolsQuery.data?.meta.total ?? 0,
    isLoading: chainsQuery.isLoading || protocolsQuery.isLoading,
    error: chainsQuery.error || protocolsQuery.error,
  };
}
