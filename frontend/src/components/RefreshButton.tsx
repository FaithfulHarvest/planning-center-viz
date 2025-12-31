import { useState, useEffect } from 'react';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';
import { dataApi } from '../services/api';
import type { RefreshJob } from '../types';

interface RefreshButtonProps {
  onRefreshComplete?: () => void;
}

export default function RefreshButton({ onRefreshComplete }: RefreshButtonProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [status, setStatus] = useState<RefreshJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check for existing running job on mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const jobStatus = await dataApi.getRefreshStatus();
        if (jobStatus.status === 'running' || jobStatus.status === 'pending') {
          setIsRefreshing(true);
          setStatus(jobStatus);
        }
      } catch {
        // No existing job, that's fine
      }
    };
    checkStatus();
  }, []);

  // Poll for status while refreshing
  useEffect(() => {
    if (!isRefreshing) return;

    const pollInterval = setInterval(async () => {
      try {
        const jobStatus = await dataApi.getRefreshStatus();
        setStatus(jobStatus);

        if (jobStatus.status === 'completed') {
          setIsRefreshing(false);
          onRefreshComplete?.();
        } else if (jobStatus.status === 'failed') {
          setIsRefreshing(false);
          setError(jobStatus.error_message || 'Data refresh failed');
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [isRefreshing, onRefreshComplete]);

  const handleRefresh = async () => {
    setError(null);
    try {
      await dataApi.startRefresh();
      setIsRefreshing(true);
    } catch (err: unknown) {
      const errorMessage = 'Failed to start data refresh';
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || errorMessage);
      } else {
        setError(errorMessage);
      }
    }
  };

  return (
    <div className="flex items-center space-x-4">
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-gradient-to-r from-accent-purple to-accent-blue hover:from-accent-purpleDark hover:to-accent-blueDark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-900 focus:ring-accent-purple disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
      >
        <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
        {isRefreshing ? 'Refreshing...' : 'Refresh Data'}
      </button>

      {isRefreshing && status && (
        <div className="text-sm text-gray-400">
          {status.current_endpoint && (
            <span>Fetching: {status.current_endpoint}</span>
          )}
          {status.total_endpoints && (
            <span className="ml-2">
              ({status.completed_endpoints}/{status.total_endpoints})
            </span>
          )}
        </div>
      )}

      {!isRefreshing && status?.status === 'completed' && (
        <div className="flex items-center text-sm text-green-400">
          <Check className="h-4 w-4 mr-1" />
          Refreshed {status.records_fetched} records
        </div>
      )}

      {error && (
        <div className="flex items-center text-sm text-red-400">
          <AlertCircle className="h-4 w-4 mr-1" />
          {error}
        </div>
      )}
    </div>
  );
}
