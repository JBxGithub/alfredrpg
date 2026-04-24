import type { ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  data: Record<string, unknown>[];
  dataKey: string;
  xAxisKey?: string;
  type?: 'line' | 'area';
  color?: string;
  children?: ReactNode;
}

const COLORS = {
  gold: '#FFD700',
  green: '#00FF88',
  blue: '#3B82F6',
  purple: '#A855F7',
};

export function ChartCard({
  title,
  subtitle,
  data,
  dataKey,
  xAxisKey = 'date',
  type = 'line',
  color = 'gold',
  children,
}: ChartCardProps) {
  const chartColor = COLORS[color as keyof typeof COLORS] || COLORS.gold;

  const formatTooltipValue = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(2)}`;
  };

  const CustomTooltip = ({ active, payload, label }: {
    active?: boolean;
    payload?: Array<{ value: number }>;
    label?: string;
  }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-dark-700 border border-dark-500 rounded p-3 shadow-lg">
          <p className="text-gray-400 text-xs mb-1">{label}</p>
          <p className="text-white font-semibold">{formatTooltipValue(payload[0].value)}</p>
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    const commonProps = {
      data,
      margin: { top: 10, right: 10, left: 0, bottom: 0 },
    };

    if (type === 'area') {
      return (
        <AreaChart {...commonProps}>
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={chartColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={chartColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a1a24" />
          <XAxis
            dataKey={xAxisKey}
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => formatTooltipValue(value)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={chartColor}
            fillOpacity={1}
            fill={`url(#gradient-${color})`}
            strokeWidth={2}
          />
        </AreaChart>
      );
    }

    return (
      <LineChart {...commonProps}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1a1a24" />
        <XAxis
          dataKey={xAxisKey}
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => formatTooltipValue(value)}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke={chartColor}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: chartColor }}
        />
      </LineChart>
    );
  };

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          {subtitle && <p className="text-gray-400 text-sm mt-1">{subtitle}</p>}
        </div>
        {children}
      </div>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
