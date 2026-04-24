import { useState } from 'react';
import { useProtocols } from '../hooks/useApi';
import { DataTable } from '../components';
import type { Column } from '../components';
import type { Protocol } from '../types';

const columns: Column<Protocol>[] = [
  { key: 'name', header: 'Protocol' },
  { key: 'category', header: 'Category' },
  { key: 'chain', header: 'Chain' },
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
    key: 'change_1d',
    header: '24h %',
    render: (item) => {
      const change = item.change_1d;
      if (change === null) return '-';
      return (
        <span className={change >= 0 ? 'text-accent-green' : 'text-red-400'}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
        </span>
      );
    },
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
];

export default function Protocols() {
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState('');
  const pageSize = 20;
  const { data, isLoading } = useProtocols({ page, page_size: pageSize, sort_by: 'tvl', order: 'desc', category: category || undefined });

  const protocols = data?.items ?? [];
  const meta = data?.meta;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Protocols</h1>
        <p className="text-gray-400 mt-1">DeFi protocols overview</p>
      </div>

      <div className="flex gap-2">
        {['', 'Lending', 'DEX', 'Yield', 'Staking'].map((cat) => (
          <button
            key={cat}
            onClick={() => { setCategory(cat); setPage(1); }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              category === cat
                ? 'bg-accent-gold text-dark-900'
                : 'bg-dark-700 text-gray-400 hover:text-white'
            }`}
          >
            {cat || 'All'}
          </button>
        ))}
      </div>

      <div className="bg-dark-800 border border-dark-600 rounded-lg p-5">
        <DataTable
          data={protocols}
          columns={columns}
          loading={isLoading}
          emptyMessage="No protocols data available"
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