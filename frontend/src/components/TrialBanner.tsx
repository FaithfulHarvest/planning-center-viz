import { Clock } from 'lucide-react';
import type { Tenant } from '../types';

interface TrialBannerProps {
  tenant: Tenant;
}

export default function TrialBanner({ tenant }: TrialBannerProps) {
  const daysRemaining = tenant.days_remaining;

  if (!tenant.is_trial_active) {
    return null;
  }

  const getBannerStyles = () => {
    if (daysRemaining <= 3) return 'bg-red-900/30 text-red-300 border-red-600/50';
    if (daysRemaining <= 7) return 'bg-yellow-900/30 text-yellow-300 border-yellow-600/50';
    return 'bg-accent-purple/20 text-accent-purpleLight border-accent-purple/50';
  };

  return (
    <div className={`${getBannerStyles()} border rounded-lg p-3 mb-6 flex items-center justify-between`}>
      <div className="flex items-center">
        <Clock className="h-5 w-5 mr-2" />
        <span className="text-sm font-medium">
          {daysRemaining === 0
            ? 'Your trial expires today!'
            : daysRemaining === 1
            ? '1 day remaining in your trial'
            : `${daysRemaining} days remaining in your free trial`}
        </span>
      </div>
    </div>
  );
}
