import { useQuery } from '@tanstack/react-query';
import { Users, CheckCircle, TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import { chartsApi } from '../services/api';

export default function SummaryCards() {
  const { data, isLoading } = useQuery({
    queryKey: ['summary'],
    queryFn: () => chartsApi.getSummary(),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6 animate-pulse">
            <div className="h-4 bg-dark-600 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-dark-600 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const cards = [
    {
      title: 'Total People',
      value: data.total_people.toLocaleString(),
      icon: Users,
      color: 'text-accent-blue',
      bgColor: 'bg-accent-blue/20',
    },
    {
      title: 'Total Check-ins',
      value: data.total_checkins.toLocaleString(),
      icon: CheckCircle,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
    },
    {
      title: 'This Week',
      value: data.checkins_this_week.toLocaleString(),
      subValue: data.week_over_week_change !== 0 && (
        <span className={`flex items-center text-sm ${data.week_over_week_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {data.week_over_week_change >= 0 ? (
            <TrendingUp className="h-4 w-4 mr-1" />
          ) : (
            <TrendingDown className="h-4 w-4 mr-1" />
          )}
          {Math.abs(data.week_over_week_change).toFixed(1)}% vs last week
        </span>
      ),
      icon: Calendar,
      color: 'text-accent-purple',
      bgColor: 'bg-accent-purple/20',
    },
    {
      title: 'Most Popular Event',
      value: data.most_popular_event || 'N/A',
      isText: true,
      icon: Calendar,
      color: 'text-accent-cyan',
      bgColor: 'bg-accent-cyan/20',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, index) => (
        <div key={index} className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-6 hover:border-accent-purple/50 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">{card.title}</p>
              <p className={`mt-1 ${card.isText ? 'text-lg' : 'text-2xl'} font-semibold text-gray-100`}>
                {card.value}
              </p>
              {card.subValue && <div className="mt-1">{card.subValue}</div>}
            </div>
            <div className={`${card.bgColor} p-3 rounded-full`}>
              <card.icon className={`h-6 w-6 ${card.color}`} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
