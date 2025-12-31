import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { chartsApi } from '../../services/api';

// Purple and blue gradient colors
const COLORS = ['#7c3aed', '#8b5cf6', '#a78bfa', '#3b82f6', '#60a5fa', '#06b6d4', '#22d3ee'];

export default function EventBreakdownChart() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['events'],
    queryFn: () => chartsApi.getEventBreakdown(),
  });

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Check-ins by Event</h3>
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-purple"></div>
        </div>
      </div>
    );
  }

  if (error || !data?.data?.length) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Check-ins by Event</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          {error ? 'Error loading data' : 'No event data available. Refresh data to get started.'}
        </div>
      </div>
    );
  }

  // Take top 7 events
  const chartData = data.data.slice(0, 7);

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6 hover:border-accent-purple/50 transition-colors">
      <h3 className="text-lg font-medium text-gray-100 mb-4">Check-ins by Event</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis type="number" fontSize={12} stroke="#9ca3af" />
            <YAxis
              type="category"
              dataKey="event_name"
              fontSize={12}
              width={120}
              tick={{ width: 120, fill: '#9ca3af' }}
              stroke="#9ca3af"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1a2e',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#f3f4f6',
              }}
              formatter={(value: number, _name: string, props: { payload: { percentage: number } }) => [
                `${value} (${props.payload.percentage}%)`,
                'Check-ins',
              ]}
            />
            <Bar dataKey="count" name="Check-ins">
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
