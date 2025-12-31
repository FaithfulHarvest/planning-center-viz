import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { chartsApi } from '../../services/api';

export default function AttendanceChart() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['attendance'],
    queryFn: () => chartsApi.getAttendance(),
  });

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Attendance Over Time</h3>
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-purple"></div>
        </div>
      </div>
    );
  }

  if (error || !data?.data?.length) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Attendance Over Time</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          {error ? 'Error loading data' : 'No attendance data available. Refresh data to get started.'}
        </div>
      </div>
    );
  }

  const chartData = data.data.map((point) => ({
    ...point,
    period: new Date(point.period).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }));

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6 hover:border-accent-purple/50 transition-colors">
      <h3 className="text-lg font-medium text-gray-100 mb-4">Attendance Over Time</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="period" fontSize={12} stroke="#9ca3af" />
            <YAxis fontSize={12} stroke="#9ca3af" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1a2e',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#f3f4f6',
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="total_checkins"
              name="Total Check-ins"
              stroke="#7c3aed"
              strokeWidth={2}
              dot={{ fill: '#7c3aed' }}
            />
            <Line
              type="monotone"
              dataKey="unique_people"
              name="Unique People"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={{ fill: '#06b6d4' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
