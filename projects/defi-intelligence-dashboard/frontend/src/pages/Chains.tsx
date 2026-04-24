import { useState } from 'react';
import { useChains } from '../hooks/useApi';
import { DataTable, LoadingSpinner } from '../components';
import type { Column } from '../components';
import type { Chain } from '../types';

const columns: Column<Chain>[] = [
  { key: 'chain_rank', header: '#', className: 'w-12' },
  { key: 'name', header: 'Chain' },
  { key: 'slug', header: 'Slug' },
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
    key: 'chain_rank',
    header: 'Rank',
    render: (item) => item.chain_rank ?? '-',
  },
];

export default function Chains() {
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const { data, isLoading } = useChains({ page, page_size: pageSize, sort_by: 'tvl', order: 'desc' });

  const chains = data?.items ?? [];
  const meta = data?.meta;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Chains</h1>
        <p className="text-gray-400 mt-1">Blockchain networks overview</p>
      </div>

      <div className="bg-dark-800 border border-dark-600 rounded-lg p-5">
        <DataTable
          data={chains}
          columns={columns}
          loading={isLoading}
          emptyMessage="No chains data available"
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