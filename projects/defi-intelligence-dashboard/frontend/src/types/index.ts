export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Chain {
  id: number;
  chain_id: string;
  name: string;
  slug: string;
  icon_url: string | null;
  tvl: number;
  chain_rank: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ChainListResponse {
  items: Chain[];
  meta: PaginationMeta;
}

export interface Protocol {
  id: number;
  protocol_id: string;
  name: string;
  slug: string;
  category: string | null;
  chain: string | null;
  icon_url: string | null;
  tvl: number;
  change_1d: number | null;
  change_7d: number | null;
  change_30d: number | null;
  mcap: number | null;
  fdv: number | null;
  listed: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface ProtocolListResponse {
  items: Protocol[];
  meta: PaginationMeta;
}

export interface TVLHistory {
  id: number;
  entity_type: string;
  entity_id: string;
  chain_id: string | null;
  date: string;
  tvl: number;
  tvl_prev_day: number | null;
  tvl_change_1d: number | null;
}

export interface TVLHistoryListResponse {
  items: TVLHistory[];
  meta: PaginationMeta;
}

export interface YieldData {
  id: number;
  pool_id: string;
  protocol_id: string | null;
  chain: string | null;
  project: string | null;
  symbol: string;
  pool: string | null;
  tvl_usd: number;
  apr: number;
  apy: number | null;
  change_1d: number | null;
  change_7d: number | null;
  outliers: number;
  il_no: number | null;
  reward_tokens: string | null;
  stablecoin: number;
  underlying_tokens: string | null;
  prediction: number;
  confidence: number | null;
  count: number;
  mu: number | null;
  sigma: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface YieldListResponse {
  items: YieldData[];
  meta: PaginationMeta;
}

export interface TopYieldResponse extends YieldListResponse {
  min_tvl: number;
  sort_by: string;
  sort_order: string;
}

export interface ApiError {
  error: string;
  message: string;
  status_code: number;
}

export interface DashboardStats {
  totalTvl: number;
  totalChains: number;
  totalProtocols: number;
  avgYield: number;
}
