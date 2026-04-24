import { useState } from 'react';
import { useYields } from '../hooks/useApi';
import { DataTable } from '../components';
import type { Column } from '../components';
import type { YieldData } from '../types';

const columns: Column<YieldData>[] = [
  { key: 'project', header: 'Protocol' },
  { key: 'chain', header: 'Chain' },
  { key: 'symbol', header: 'Symbol' },
  {
    key: 'pool',
    header: 'Pool',
    render: (item) => item.pool ?? '-',
  },
  {
    key: 'tvl_usd',
    header: 'TVL',
    render: (item) => (
      <span className="text-accent-gold">
        ${item.tvl_usd >= 1e6 ? `${(item.tvl_usd / 1e6).toFixed(2)}M` : item.tvl_usd >= 1e3 ? `${(item.tvl_usd / 1e3).toFixed(2)}K` : item.tvl_usd.toFixed(0)}
      </span>
    ),
  },
  {
    key: 'apy',
    header: 'APY',
    render: (item) => (
      <span className="text-accent-green font-medium">
        {item.apy?.toFixed(2) ?? '-'}%
      </span>
    ),
  },
  {
    key: 'change_7d',
    header: '7d %',
    render: (item) => {
      const change = item.change_7d;
      if (change === null) return '-';
      return (
        <span className={change >= 0 ? 'text-accent-green' : 'text-red-400'}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
        </span>
      );
    },
  },
  {
    key: 'stablecoin',
    header: 'Stable',
    render: (item) => (item.stablecoin ? 'Yes' : 'No'),
  },
];

export default function Yields() {
  const [page, setPage] = useState(1);
  const [chain, setChain] = useState('');
  const [minTvl, setMinTvl] = useState('');
  const pageSize = 20;
  
  const { data, isLoading } = useYields({
    page,
    page_size: pageSize,
    chain: chain || undefined,
    min_tvl: minTvl ? parseFloat(minTvl) : undefined,
  });

  const yields = data?.items ?? [];
  const meta = data?.meta;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Yields</h1>
        <p className="text-gray-400 mt-1">Yield farming opportunities</p>
      </div>

      <div className="flex flex-wrap gap-4">
        <input
          type="text"
          placeholder="Filter by chain..."
          value={chain}
          onChange={(e) => { setChain(e.target.value); setPage(1); }}
          className="px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent-gold"
        />
        <input
          type="number"
          placeholder="Min TVL (USD)"
          value={minTvl}
          onChange={(e) => { setMinTvl(e.target.value); setPage(1); }}
          className="px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-accent-gold"
        />
      </div>

      <div className="bg-dark-800 border border-dark-600 rounded-lg p-5">
        <DataTable
          data={yields}
          columns={columns}
          loading={isLoading}
          emptyMessage="No yields data available"
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