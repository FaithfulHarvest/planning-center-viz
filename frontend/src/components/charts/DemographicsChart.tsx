import { useQuery } from '@tanstack/react-query';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { chartsApi } from '../../services/api';

// Purple/blue gender colors
const GENDER_COLORS = ['#3b82f6', '#ec4899', '#6b7280'];
// Gradient age colors
const AGE_COLORS = ['#7c3aed', '#8b5cf6', '#a78bfa', '#c4b5fd', '#3b82f6', '#60a5fa', '#93c5fd'];

export default function DemographicsChart() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['demographics'],
    queryFn: () => chartsApi.getDemographics(),
  });

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Demographics</h3>
        <div className="h-80 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-purple"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Demographics</h3>
        <div className="h-80 flex items-center justify-center text-gray-500">
          {error ? 'Error loading data' : 'No demographics data available. Refresh data to get started.'}
        </div>
      </div>
    );
  }

  const hasGenderData = data.gender_distribution && data.gender_distribution.length > 0;
  const hasAgeData = data.age_groups && data.age_groups.length > 0;

  if (!hasGenderData && !hasAgeData) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Demographics</h3>
        <div className="h-80 flex items-center justify-center text-gray-500">
          No demographics data available. Refresh data to get started.
        </div>
      </div>
    );
  }

  const tooltipStyle = {
    backgroundColor: '#1a1a2e',
    border: '1px solid #374151',
    borderRadius: '8px',
    color: '#f3f4f6',
  };

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6 hover:border-accent-purple/50 transition-colors">
      <h3 className="text-lg font-medium text-gray-100 mb-4">
        Demographics ({data.total_people.toLocaleString()} people)
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Gender Distribution */}
        {hasGenderData && (
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-2 text-center">Gender Distribution</h4>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.gender_distribution}
                    dataKey="count"
                    nameKey="gender"
                    cx="50%"
                    cy="50%"
                    outerRadius={60}
                    label={({ gender, percentage }) => `${gender} (${percentage}%)`}
                    labelLine={false}
                  >
                    {data.gender_distribution.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={GENDER_COLORS[index % GENDER_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [value.toLocaleString(), 'Count']}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Age Distribution */}
        {hasAgeData && (
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-2 text-center">Age Distribution</h4>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.age_groups}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="age_group"
                    fontSize={10}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                    stroke="#9ca3af"
                  />
                  <YAxis fontSize={12} stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [value.toLocaleString(), 'Count']}
                  />
                  <Bar dataKey="count" name="People">
                    {data.age_groups.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={AGE_COLORS[index % AGE_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
