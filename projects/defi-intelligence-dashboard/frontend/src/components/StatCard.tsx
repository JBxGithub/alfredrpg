import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number | null;
  icon?: ReactNode;
  format?: 'number' | 'currency' | 'percent';
}

export function StatCard({ title, value, change, icon, format = 'number' }: StatCardProps) {
  const formatValue = (val: string | number) => {
    if (typeof val === 'string') return val;
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          maximumFractionDigits: 0,
        }).format(val);
      case 'percent':
        return `${val.toFixed(2)}%`;
      default:
        return new Intl.NumberFormat('en-US').format(val);
    }
  };

  const getTrendIcon = () => {
    if (change === null || change === undefined) return null;
    if (change > 0) return <TrendingUp className="w-4 h-4 text-accent-green" />;
    if (change < 0) return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getTrendColor = () => {
    if (change === null || change === undefined) return 'text-gray-400';
    if (change > 0) return 'text-accent-green';
    if (change < 0) return 'text-red-400';
    return 'text-gray-400';
  };

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg p-5 hover:border-dark-500 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <span className="text-gray-400 text-sm font-medium">{title}</span>
        {icon && <div className="text-accent-gold">{icon}</div>}
      </div>
      <div className="flex items-end gap-3">
        <span className="text-2xl font-bold text-white">{formatValue(value)}</span>
        {change !== undefined && (
          <div className={`flex items-center gap-1 ${getTrendColor()}`}>
            {getTrendIcon()}
            <span className="text-sm font-medium">
              {change !== null ? `${change > 0 ? '+' : ''}${change.toFixed(2)}%` : '-'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
