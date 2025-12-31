import axios from 'axios';
import type {
  AuthToken,
  User,
  Tenant,
  RefreshJob,
  AttendanceDataPoint,
  EventBreakdown,
  DemographicsData,
  SummaryStats,
  ChartResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  signup: async (data: {
    church_name: string;
    city: string;
    state: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    pco_app_id?: string;
    pco_secret?: string;
  }): Promise<AuthToken> => {
    const response = await api.post('/auth/signup', data);
    return response.data;
  },

  login: async (email: string, password: string): Promise<AuthToken> => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Tenant API
export const tenantApi = {
  getTenant: async (): Promise<Tenant> => {
    const response = await api.get('/tenant');
    return response.data;
  },

  updateTenant: async (data: { name?: string; data_timezone?: string }): Promise<Tenant> => {
    const response = await api.put('/tenant', data);
    return response.data;
  },

  updateCredentials: async (pco_app_id: string, pco_secret: string): Promise<Tenant> => {
    const response = await api.put('/tenant/credentials', { pco_app_id, pco_secret });
    return response.data;
  },

  testCredentials: async (pco_app_id: string, pco_secret: string): Promise<{
    success: boolean;
    message: string;
    services_available?: string[];
  }> => {
    const response = await api.post('/tenant/test-credentials', { pco_app_id, pco_secret });
    return response.data;
  },
};

// Data API
export const dataApi = {
  startRefresh: async (): Promise<{ job_id: string; status: string; message: string }> => {
    const response = await api.post('/data/refresh');
    return response.data;
  },

  getRefreshStatus: async (): Promise<RefreshJob> => {
    const response = await api.get('/data/refresh/status');
    return response.data;
  },

  getRefreshHistory: async (limit = 10): Promise<RefreshJob[]> => {
    const response = await api.get(`/data/refresh/history?limit=${limit}`);
    return response.data;
  },
};

// Charts API
export const chartsApi = {
  getAttendance: async (
    startDate?: string,
    endDate?: string,
    granularity = 'week'
  ): Promise<ChartResponse<AttendanceDataPoint>> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    params.append('granularity', granularity);

    const response = await api.get(`/charts/attendance?${params.toString()}`);
    return response.data;
  },

  getEventBreakdown: async (
    startDate?: string,
    endDate?: string
  ): Promise<ChartResponse<EventBreakdown>> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await api.get(`/charts/events?${params.toString()}`);
    return response.data;
  },

  getDemographics: async (): Promise<DemographicsData> => {
    const response = await api.get('/charts/demographics');
    return response.data;
  },

  getSummary: async (): Promise<SummaryStats> => {
    const response = await api.get('/charts/summary');
    return response.data;
  },
};

// Data Viewer API
export interface TableInfo {
  name: string;
  row_count: number;
}

export interface ColumnInfo {
  name: string;
  data_type: string;
  is_nullable: boolean;
}

export interface TableDataResponse {
  columns: string[];
  rows: Record<string, unknown>[];
  total_count: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface DistinctValuesResponse {
  column: string;
  values: (string | number | boolean)[];
  total_count: number;
}

export type FilterValue = string | string[] | { from?: string; to?: string };

export const viewerApi = {
  getTables: async (): Promise<TableInfo[]> => {
    const response = await api.get('/viewer/tables');
    return response.data;
  },

  getTableColumns: async (tableName: string): Promise<ColumnInfo[]> => {
    const response = await api.get(`/viewer/tables/${tableName}/columns`);
    return response.data;
  },

  getDistinctValues: async (
    tableName: string,
    columnName: string,
    search?: string,
    limit = 100,
    filters?: Record<string, FilterValue>
  ): Promise<DistinctValuesResponse> => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', limit.toString());
    if (filters && Object.keys(filters).length > 0) {
      params.append('filters', JSON.stringify(filters));
    }
    const response = await api.get(
      `/viewer/tables/${tableName}/columns/${columnName}/distinct?${params.toString()}`
    );
    return response.data;
  },

  getTableData: async (
    tableName: string,
    options: {
      columns?: string[];
      filters?: Record<string, FilterValue>;
      page?: number;
      perPage?: number;
    } = {}
  ): Promise<TableDataResponse> => {
    const params = new URLSearchParams();
    if (options.columns && options.columns.length > 0) {
      params.append('columns', options.columns.join(','));
    }
    if (options.filters && Object.keys(options.filters).length > 0) {
      params.append('filters', JSON.stringify(options.filters));
    }
    if (options.page) params.append('page', options.page.toString());
    if (options.perPage) params.append('per_page', options.perPage.toString());

    const response = await api.get(`/viewer/tables/${tableName}/data?${params.toString()}`);
    return response.data;
  },
};

export default api;
