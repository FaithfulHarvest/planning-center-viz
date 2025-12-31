import { Link } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { Settings, LogOut, AlertCircle, Database } from 'lucide-react';
import TrialBanner from '../components/TrialBanner';
import RefreshButton from '../components/RefreshButton';
import SummaryCards from '../components/SummaryCards';
import AttendanceChart from '../components/charts/AttendanceChart';
import EventBreakdownChart from '../components/charts/EventBreakdownChart';
import DemographicsChart from '../components/charts/DemographicsChart';

export default function DashboardPage() {
  const { user, tenant, logout } = useAuth();
  const queryClient = useQueryClient();

  const handleRefreshComplete = () => {
    // Invalidate all chart queries to refresh data
    queryClient.invalidateQueries({ queryKey: ['attendance'] });
    queryClient.invalidateQueries({ queryKey: ['events'] });
    queryClient.invalidateQueries({ queryKey: ['demographics'] });
    queryClient.invalidateQueries({ queryKey: ['summary'] });
  };

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="bg-dark-800 border-b border-dark-500 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-accent-purple to-accent-blue">
                {tenant?.name}
              </h1>
              <p className="text-sm text-gray-400">Welcome back, {user?.first_name || user?.email}</p>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/data"
                className="inline-flex items-center px-3 py-2 border border-dark-500 shadow-sm text-sm font-medium rounded-md text-gray-300 bg-dark-700 hover:bg-dark-600 hover:border-accent-purple transition-colors"
              >
                <Database className="h-4 w-4 mr-2" />
                Data Viewer
              </Link>
              <Link
                to="/settings"
                className="inline-flex items-center px-3 py-2 border border-dark-500 shadow-sm text-sm font-medium rounded-md text-gray-300 bg-dark-700 hover:bg-dark-600 hover:border-accent-purple transition-colors"
              >
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Link>
              <button
                onClick={logout}
                className="inline-flex items-center px-3 py-2 border border-dark-500 shadow-sm text-sm font-medium rounded-md text-gray-300 bg-dark-700 hover:bg-dark-600 hover:border-accent-purple transition-colors"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Trial Banner */}
        {tenant && <TrialBanner tenant={tenant} />}

        {/* Credentials Warning */}
        {tenant && !tenant.has_credentials && (
          <div className="bg-yellow-900/30 border border-yellow-600/50 rounded-lg p-4 mb-6 flex items-start">
            <AlertCircle className="h-5 w-5 text-yellow-500 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-yellow-400">Planning Center credentials required</h3>
              <p className="mt-1 text-sm text-yellow-300/80">
                Add your Planning Center API credentials in{' '}
                <Link to="/settings" className="underline font-medium text-yellow-400 hover:text-yellow-300">
                  Settings
                </Link>{' '}
                to start syncing data.
              </p>
            </div>
          </div>
        )}

        {/* Refresh Button and Last Updated */}
        <div className="flex items-center justify-between mb-6">
          <RefreshButton onRefreshComplete={handleRefreshComplete} />
          {tenant?.last_data_refresh && (
            <p className="text-sm text-gray-500">
              Last refreshed: {new Date(tenant.last_data_refresh).toLocaleString()}
            </p>
          )}
        </div>

        {/* Summary Cards */}
        <SummaryCards />

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <AttendanceChart />
          <EventBreakdownChart />
        </div>

        {/* Demographics - Full Width */}
        <DemographicsChart />
      </main>
    </div>
  );
}
