import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserPlus } from 'lucide-react';

export default function SignupPage() {
  const { signup } = useAuth();
  const [formData, setFormData] = useState({
    church_name: '',
    city: '',
    state: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    pco_app_id: '',
    pco_secret: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      await signup({
        church_name: formData.church_name,
        city: formData.city,
        state: formData.state,
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name || undefined,
        last_name: formData.last_name || undefined,
        pco_app_id: formData.pco_app_id || undefined,
        pco_secret: formData.pco_secret || undefined,
      });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create account';
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || errorMessage);
      } else {
        setError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const inputClasses = "mt-1 appearance-none relative block w-full px-3 py-2 border border-dark-500 placeholder-gray-500 text-gray-100 bg-dark-700 rounded-md focus:outline-none focus:ring-accent-purple focus:border-accent-purple sm:text-sm";

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="text-center text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-accent-purple to-accent-blue">
            Planning Center Viz
          </h1>
          <h2 className="mt-6 text-center text-xl font-semibold text-gray-100">
            Start your free 2-week trial
          </h2>
          <p className="mt-2 text-center text-sm text-gray-400">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-accent-purple hover:text-accent-purpleLight">
              Sign in
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-900/50 border border-red-500 p-4">
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="church_name" className="block text-sm font-medium text-gray-300">
                Church Name *
              </label>
              <input
                id="church_name"
                name="church_name"
                type="text"
                required
                className={inputClasses}
                placeholder="First Church of Example"
                value={formData.church_name}
                onChange={handleChange}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="city" className="block text-sm font-medium text-gray-300">
                  City *
                </label>
                <input
                  id="city"
                  name="city"
                  type="text"
                  required
                  className={inputClasses}
                  placeholder="Paradise"
                  value={formData.city}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label htmlFor="state" className="block text-sm font-medium text-gray-300">
                  State *
                </label>
                <input
                  id="state"
                  name="state"
                  type="text"
                  required
                  maxLength={2}
                  className={`${inputClasses} uppercase`}
                  placeholder="TX"
                  value={formData.state}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-300">
                  First Name
                </label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  className={inputClasses}
                  value={formData.first_name}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-300">
                  Last Name
                </label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  className={inputClasses}
                  value={formData.last_name}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300">
                Email Address *
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className={inputClasses}
                placeholder="admin@yourchurch.com"
                value={formData.email}
                onChange={handleChange}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-300">
                  Password *
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className={inputClasses}
                  value={formData.password}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300">
                  Confirm Password *
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  className={inputClasses}
                  value={formData.confirmPassword}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="border-t border-dark-500 pt-4 mt-4">
              <p className="text-sm text-gray-400 mb-3">
                Planning Center API Credentials (optional - can be added later)
              </p>
              <div className="space-y-4">
                <div>
                  <label htmlFor="pco_app_id" className="block text-sm font-medium text-gray-300">
                    PCO App ID
                  </label>
                  <input
                    id="pco_app_id"
                    name="pco_app_id"
                    type="text"
                    className={inputClasses}
                    value={formData.pco_app_id}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label htmlFor="pco_secret" className="block text-sm font-medium text-gray-300">
                    PCO Secret
                  </label>
                  <input
                    id="pco_secret"
                    name="pco_secret"
                    type="password"
                    className={inputClasses}
                    value={formData.pco_secret}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-to-r from-accent-purple to-accent-blue hover:from-accent-purpleDark hover:to-accent-blueDark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-900 focus:ring-accent-purple disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                <UserPlus className="h-5 w-5 text-accent-purpleLight group-hover:text-white" />
              </span>
              {isLoading ? 'Creating account...' : 'Start Free Trial'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
