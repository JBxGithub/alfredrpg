import { useChains, useProtocols, useTopYields } from '../hooks/useApi';
import { StatCard, ChartCard, DataTable, LoadingSpinner } from '../components';
import { TrendingUp, Link2, Shield, Percent } from 'lucide-react';
import type { Column } from '../components';
import type { Chain, YieldData } from '../types';

const chainColumns: Column<Chain>[] = [
  { key: 'chain_rank', header: '#', className: 'w-12' },
  { key: 'name', header: 'Chain' },
  {
    key: 'tvl',
    header: 'TVL',
    render: (item) => (
      <span className="text-accent-gold font-medium">
        ${(item.tvl / 1e9).toFixed(2)}B
      </span>
    ),
  },
];

const yieldColumns: Column<YieldData>[] = [
  { key: 'project', header: 'Protocol' },
  { key: 'chain', header: 'Chain' },
  {
    key: 'symbol',
    header: 'Symbol',
    render: (item) => (
      <span className="text-accent-gold">{item.symbol}</span>
    ),
  },
  {
    key: 'apy',
    header: 'APY',
    render: (item) => (
      <span className="text-accent-green font-medium">
        {item.apy?.toFixed(2)}%
      </span>
    ),
  },
  {
    key: 'tvl_usd',
    header: 'TVL',
    render: (item) => `$${(item.tvl_usd / 1e6).toFixed(2)}M`,
  },
];

export default function Dashboard() {
  const chainsQuery = useChains({ page: 1, page_size: 10, sort_by: 'tvl', order: 'desc' });
  const protocolsQuery = useProtocols({ page: 1, page_size: 10, sort_by: 'tvl', order: 'desc' });
  const yieldsQuery = useTopYields({ page: 1, page_size: 10, sort_by: 'apy', min_tvl: 1e6 });

  const totalChains = chainsQuery.data?.meta.total ?? 0;
  const totalProtocols = protocolsQuery.data?.meta.total ?? 0;
  const avgYield = yieldsQuery.data?.items.length 
    ? yieldsQuery.data.items.reduce((sum, y) => sum + (y.apy ?? 0), 0) / yieldsQuery.data.items.length 
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">DeFi Intelligence Overview</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total TVL"
          value="$142.5B"
          change={2.34}
          icon={<TrendingUp className="w-5 h-5" />}
          format="currency"
        />
        <StatCard
          title="Active Chains"
          value={totalChains}
          icon={<Link2 className="w-5 h-5" />}
        />
        <StatCard
          title="Protocols"
          value={totalProtocols}
          icon={<Shield className="w-5 h-5" />}
        />
        <StatCard
          title="Avg Yield (Top 10)"
          value={avgYield.toFixed(2)}
          change={0.5}
          icon={<Percent className="w-5 h-5" />}
          format="percent"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Top Chains by TVL"
          subtitle="Top 10 blockchain networks"
          data={chainsQuery.data?.items.slice(0, 10).map(c => ({
            name: c.name,
            tvl: c.tvl,
          })) ?? []}
          dataKey="tvl"
          xAxisKey="name"
          type="area"
          color="gold"
        />
        
        <div className="bg-dark-800 border border-dark-600 rounded-lg p-5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Top Yields</h3>
              <p className="text-gray-400 text-sm mt-1">Highest APY pools (TVL &gt; $1M)</p>
            </div>
          </div>
          {yieldsQuery.isLoading ? (
            <LoadingSpinner />
          ) : (
            <DataTable
              data={yieldsQuery.data?.items ?? []}
              columns={yieldColumns}
              loading={yieldsQuery.isLoading}
            />
          )}
        </div>
      </div>

      <div className="bg-dark-800 border border-dark-600 rounded-lg p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Top Chains</h3>
            <p className="text-gray-400 text-sm mt-1">Blockchain networks by total value locked</p>
          </div>
        </div>
        <DataTable
          data={chainsQuery.data?.items ?? []}
          columns={chainColumns}
          loading={chainsQuery.isLoading}
          emptyMessage="No chains data available"
        />
      </div>
    </div>
  );
}