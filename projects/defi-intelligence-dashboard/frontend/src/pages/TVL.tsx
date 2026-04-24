import { useState } from 'react';
import { useTVLHistory } from '../hooks/useApi';
import { ChartCard, DataTable } from '../components';
import type { Column } from '../components';
import type { TVLHistory } from '../types';

const columns: Column<TVLHistory>[] = [
  { key: 'date', header: 'Date' },
  {
    key: 'entity_type',
    header: 'Type',
    render: (item) => (
      <span className="text-accent-gold capitalize">{item.entity_type}</span>
    ),
  },
  { key: 'entity_id', header: 'Entity' },
  { key: 'chain_id', header: 'Chain' },
  {
    key: 'tvl',
    header: 'TVL',
    render: (item) => (
      <span className="text-accent-gold font-medium">
        ${item.tvl >= 1e9 ? `${(item.tvl / 1e9).toFixed(2)}B` : item.tvl >= 1e6 ? `${(item.tvl / 1e6).toFixed(2)}M` : item.tvl.toLocaleString()}
      </span>
    ),
  },
  {
    key: 'tvl_change_1d',
    header: '24h %',
    render: (item) => {
      const change = item.tvl_change_1d;
      if (change === null) return '-';
      return (
        <span className={change >= 0 ? 'text-accent-green' : 'text-red-400'}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
        </span>
      );
    },
  },
];

export default function TVL() {
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  const { data, isLoading } = useTVLHistory({
    entity_type: entityType || undefined,
    entity_id: entityId || undefined,
    start_date: startDate,
    end_date: endDate,
    page,
    page_size: pageSize,
  });

  const tvlData = data?.items ?? [];
  const meta = data?.meta;

  const chartData = tvlData
    .slice(0, 30)
    .reverse()
    .map((item) => ({
      date: item.date,
      tvl: item.tvl,
    }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">TVL History</h1>
        <p className="text-gray-400 mt-1">Total Value Locked historical data</p>
      </div>

      <div className="flex flex-wrap gap-4">
        <select
          value={entityType}
          onChange={(e) => { setEntityType(e.target.value); setPage(1); }}
          className="px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-gold"
        >
          <option value="">All Types</option>
          <option value="chain">Chain</option>
          <option value="protocol">Protocol</option>
        </select>
        <input
          type="text"
          placeholder="Entity ID (e.g., ethereum)"
          value={entityId}
          onChange={(e) => { setEntityId(e.target.value); setPage(1); }}
          className="px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent-gold"
        />
      </div>

      {chartData.length > 0 && (
        <ChartCard
          title="TVL Trend"
          subtitle="Last 30 days"
          data={chartData}
          dataKey="tvl"
          xAxisKey="date"
          type="area"
          color="green"
        />
      )}

      <div className="bg-dark-800 border border-dark-600 rounded-lg p-5">
        <DataTable
          data={tvlData}
          columns={columns}
          loading={isLoading}
          emptyMessage="No TVL history data available"
        />
        
        {meta && (
          <div className="flex items-center justify-center gap-2 mt-4">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 rounded bg-dark-700 text-gray-400 hover:text-white hover:bg-dark-600 disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-gray-400">
              Page {page} of {meta.total_pages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(meta.total_pages, p + 1))}
              disabled={page >= meta.total_pages}
              className="px-4 py-2 rounded bg-dark-700 text-gray-400 hover:text-white hover:bg-dark-600 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}