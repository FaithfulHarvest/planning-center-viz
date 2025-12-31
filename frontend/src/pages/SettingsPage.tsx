import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Save, CheckCircle, AlertCircle, Globe } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { tenantApi } from '../services/api';

// Common US timezones for churches
const TIMEZONE_OPTIONS = [
  { value: 'US/Eastern', label: 'Eastern Time (ET)' },
  { value: 'US/Central', label: 'Central Time (CT)' },
  { value: 'US/Mountain', label: 'Mountain Time (MT)' },
  { value: 'US/Pacific', label: 'Pacific Time (PT)' },
  { value: 'US/Alaska', label: 'Alaska Time (AKT)' },
  { value: 'US/Hawaii', label: 'Hawaii Time (HT)' },
  { value: 'US/Arizona', label: 'Arizona (no DST)' },
  { value: 'America/Puerto_Rico', label: 'Puerto Rico (AST)' },
];

export default function SettingsPage() {
  const { tenant, refreshTenant } = useAuth();
  const [pcoAppId, setPcoAppId] = useState('');
  const [pcoSecret, setPcoSecret] = useState('');
  const [selectedTimezone, setSelectedTimezone] = useState(tenant?.data_timezone || 'US/Central');
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isSavingTimezone, setIsSavingTimezone] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [timezoneMessage, setTimezoneMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    services?: string[];
  } | null>(null);

  const handleTest = async () => {
    if (!pcoAppId || !pcoSecret) {
      setMessage({ type: 'error', text: 'Please enter both App ID and Secret' });
      return;
    }

    setIsTesting(true);
    setTestResult(null);
    setMessage(null);

    try {
      const result = await tenantApi.testCredentials(pcoAppId, pcoSecret);
      setTestResult(result);
    } catch {
      setTestResult({ success: false, message: 'Failed to test credentials' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    if (!pcoAppId || !pcoSecret) {
      setMessage({ type: 'error', text: 'Please enter both App ID and Secret' });
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      await tenantApi.updateCredentials(pcoAppId, pcoSecret);
      await refreshTenant();
      setMessage({ type: 'success', text: 'Credentials saved successfully!' });
      setPcoAppId('');
      setPcoSecret('');
      setTestResult(null);
    } catch {
      setMessage({ type: 'error', text: 'Failed to save credentials' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveTimezone = async () => {
    setIsSavingTimezone(true);
    setTimezoneMessage(null);

    try {
      await tenantApi.updateTenant({ data_timezone: selectedTimezone });
      await refreshTenant();
      setTimezoneMessage({ type: 'success', text: 'Timezone saved! Run a data refresh to apply.' });
    } catch {
      setTimezoneMessage({ type: 'error', text: 'Failed to save timezone' });
    } finally {
      setIsSavingTimezone(false);
    }
  };

  const inputClasses = "mt-1 block w-full px-3 py-2 border border-dark-500 bg-dark-700 text-gray-100 placeholder-gray-500 rounded-md shadow-sm focus:outline-none focus:ring-accent-purple focus:border-accent-purple sm:text-sm";

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="bg-dark-800 border-b border-dark-500 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center">
            <Link
              to="/dashboard"
              className="inline-flex items-center text-gray-400 hover:text-gray-200 mr-4"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-accent-purple to-accent-blue">
              Settings
            </h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Account Info */}
        <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 mb-6">
          <div className="px-6 py-4 border-b border-dark-500">
            <h2 className="text-lg font-medium text-gray-100">Account Information</h2>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400">Church Name</label>
              <p className="mt-1 text-sm text-gray-100">{tenant?.name}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400">Trial Status</label>
              <p className="mt-1 text-sm">
                {tenant?.is_trial_active ? (
                  <span className="text-green-400">{tenant.days_remaining} days remaining</span>
                ) : (
                  <span className="text-red-400">Expired</span>
                )}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400">Credentials Status</label>
              <p className="mt-1 text-sm">
                {tenant?.has_credentials ? (
                  <span className="flex items-center text-green-400">
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Configured
                  </span>
                ) : (
                  <span className="flex items-center text-yellow-400">
                    <AlertCircle className="h-4 w-4 mr-1" />
                    Not configured
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Data Settings */}
        <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 mb-6">
          <div className="px-6 py-4 border-b border-dark-500">
            <h2 className="text-lg font-medium text-gray-100 flex items-center">
              <Globe className="h-5 w-5 mr-2 text-accent-purple" />
              Data Settings
            </h2>
            <p className="mt-1 text-sm text-gray-400">
              Configure how your Planning Center data is processed and displayed.
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            {timezoneMessage && (
              <div
                className={`rounded-md p-4 border ${
                  timezoneMessage.type === 'success'
                    ? 'bg-green-900/30 border-green-600/50'
                    : 'bg-red-900/30 border-red-600/50'
                }`}
              >
                <p
                  className={`text-sm ${
                    timezoneMessage.type === 'success' ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {timezoneMessage.text}
                </p>
              </div>
            )}

            <div>
              <label htmlFor="timezone" className="block text-sm font-medium text-gray-300">
                Timezone
              </label>
              <p className="text-xs text-gray-500 mb-2">
                All timestamps will be converted to this timezone when data is refreshed.
              </p>
              <div className="flex items-center gap-3">
                <select
                  id="timezone"
                  value={selectedTimezone}
                  onChange={(e) => setSelectedTimezone(e.target.value)}
                  className={inputClasses + " flex-1"}
                >
                  {TIMEZONE_OPTIONS.map((tz) => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleSaveTimezone}
                  disabled={isSavingTimezone || selectedTimezone === tenant?.data_timezone}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-gradient-to-r from-accent-purple to-accent-blue hover:from-accent-purpleDark hover:to-accent-blueDark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-900 focus:ring-accent-purple disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isSavingTimezone ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Planning Center Credentials */}
        <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500">
          <div className="px-6 py-4 border-b border-dark-500">
            <h2 className="text-lg font-medium text-gray-100">Planning Center API Credentials</h2>
            <p className="mt-1 text-sm text-gray-400">
              Enter your Planning Center API credentials to sync your data.{' '}
              <a
                href="https://api.planningcenteronline.com/oauth/applications"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-purple hover:text-accent-purpleLight underline"
              >
                Get your API credentials
              </a>
            </p>
          </div>
          <div className="px-6 py-4 space-y-4">
            {message && (
              <div
                className={`rounded-md p-4 border ${
                  message.type === 'success'
                    ? 'bg-green-900/30 border-green-600/50'
                    : 'bg-red-900/30 border-red-600/50'
                }`}
              >
                <p
                  className={`text-sm ${
                    message.type === 'success' ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {message.text}
                </p>
              </div>
            )}

            <div>
              <label htmlFor="pco_app_id" className="block text-sm font-medium text-gray-300">
                App ID
              </label>
              <input
                id="pco_app_id"
                type="text"
                className={inputClasses}
                value={pcoAppId}
                onChange={(e) => setPcoAppId(e.target.value)}
                placeholder="Enter your Planning Center App ID"
              />
            </div>

            <div>
              <label htmlFor="pco_secret" className="block text-sm font-medium text-gray-300">
                Secret
              </label>
              <input
                id="pco_secret"
                type="password"
                className={inputClasses}
                value={pcoSecret}
                onChange={(e) => setPcoSecret(e.target.value)}
                placeholder="Enter your Planning Center Secret"
              />
            </div>

            {testResult && (
              <div
                className={`rounded-md p-4 border ${
                  testResult.success
                    ? 'bg-green-900/30 border-green-600/50'
                    : 'bg-red-900/30 border-red-600/50'
                }`}
              >
                <div className="flex items-start">
                  {testResult.success ? (
                    <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
                  )}
                  <div>
                    <p
                      className={`text-sm font-medium ${
                        testResult.success ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {testResult.message}
                    </p>
                    {testResult.services && testResult.services.length > 0 && (
                      <p className="mt-1 text-sm text-green-300">
                        Available services: {testResult.services.join(', ')}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-3 pt-4">
              <button
                onClick={handleTest}
                disabled={isTesting || !pcoAppId || !pcoSecret}
                className="inline-flex items-center px-4 py-2 border border-dark-500 shadow-sm text-sm font-medium rounded-md text-gray-300 bg-dark-700 hover:bg-dark-600 hover:border-accent-purple focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-900 focus:ring-accent-purple disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isTesting ? 'Testing...' : 'Test Connection'}
              </button>
              <button
                onClick={handleSave}
                disabled={isLoading || !pcoAppId || !pcoSecret}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-gradient-to-r from-accent-purple to-accent-blue hover:from-accent-purpleDark hover:to-accent-blueDark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-900 focus:ring-accent-purple disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <Save className="h-4 w-4 mr-2" />
                {isLoading ? 'Saving...' : 'Save Credentials'}
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
