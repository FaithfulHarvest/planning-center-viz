import { useAuth } from '../context/AuthContext';
import { Clock, LogOut } from 'lucide-react';

export default function TrialExpiredPage() {
  const { logout, tenant } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 text-center">
        <div>
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-yellow-100">
            <Clock className="h-8 w-8 text-yellow-600" />
          </div>
          <h1 className="mt-6 text-3xl font-bold text-gray-900">Trial Expired</h1>
          <p className="mt-4 text-gray-600">
            Your 2-week free trial for <strong>{tenant?.name}</strong> has ended.
          </p>
          <p className="mt-2 text-gray-600">
            Contact us to continue using Planning Center Viz with a paid subscription.
          </p>
        </div>

        <div className="bg-gray-100 rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900">What's next?</h2>
          <ul className="mt-4 text-left text-sm text-gray-600 space-y-2">
            <li>- Email us at <strong>support@example.com</strong></li>
            <li>- We'll help you set up a subscription plan</li>
            <li>- Your data is safe and will be available once you subscribe</li>
          </ul>
        </div>

        <button
          onClick={logout}
          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </button>
      </div>
    </div>
  );
}
