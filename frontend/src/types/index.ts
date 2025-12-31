// User and Auth types
export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_admin: boolean;
  tenant_id: string;
  created_at: string;
}

export interface Tenant {
  id: string;
  name: string;
  trial_start_date: string;
  trial_end_date: string;
  is_trial_active: boolean;
  days_remaining: number;
  is_locked: boolean;
  has_credentials: boolean;
  last_data_refresh?: string;
  created_at: string;
  data_timezone: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

// Refresh job types
export interface RefreshJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  total_endpoints?: number;
  completed_endpoints: number;
  current_endpoint?: string;
  records_fetched: number;
  error_message?: string;
}

// Chart data types
export interface AttendanceDataPoint {
  period: string;
  total_checkins: number;
  unique_people: number;
}

export interface EventBreakdown {
  event_name: string;
  count: number;
  percentage: number;
}

export interface AgeGroup {
  age_group: string;
  count: number;
  percentage: number;
}

export interface GenderDistribution {
  gender: string;
  count: number;
  percentage: number;
}

export interface DemographicsData {
  age_groups: AgeGroup[];
  gender_distribution: GenderDistribution[];
  total_people: number;
}

export interface SummaryStats {
  total_people: number;
  total_checkins: number;
  checkins_this_week: number;
  checkins_last_week: number;
  week_over_week_change: number;
  most_popular_event?: string;
}

// API response wrapper
export interface ChartResponse<T> {
  data: T[];
  metadata?: Record<string, unknown>;
}
