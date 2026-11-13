const API_BASE_URL = typeof window !== 'undefined' && window.location.port === '5173'
  ? 'http://localhost:5000/api'
  : '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  try {
    const response = await fetch(url, { ...options, headers });
    const data = await response.json();
    if (!response.ok) {
      throw { status: response.status, data };
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // Health
  checkHealth: () => request('/health'),

  // Auth
  login: (username, password) => request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  }),
  register: (userData) => request('/auth/register', {
    method: 'POST',
    body: JSON.stringify(userData)
  }),
  getCurrentUser: () => request('/auth/me'),

  // DFA
  simulateDFA: (report_id) => request('/dfa/simulate', {
    method: 'POST',
    body: JSON.stringify({ report_id })
  }),
  getDFAInfo: () => request('/dfa/info'),
  generateReportId: () => request('/dfa/generate-id'),

  // Reports
  submitReport: (reportData) => request('/reports/submit', {
    method: 'POST',
    body: JSON.stringify(reportData)
  }),
  previewClassification: (description) => request('/reports/preview-classification', {
    method: 'POST',
    body: JSON.stringify({ description })
  }),
  getReports: (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.zone) params.append('zone', filters.zone);
    if (filters.category) params.append('category', filters.category);
    if (filters.priority) params.append('priority', filters.priority);
    if (filters.q) params.append('q', filters.q);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request(`/reports${qs}`);
  },
  getReportById: (idOrCode) => request(`/reports/${idOrCode}`),
  updateReport: (idOrCode, updateData) => request(`/reports/${idOrCode}`, {
    method: 'PUT',
    body: JSON.stringify(updateData)
  }),

  // Dispatch
  triggerDispatch: (reportId, updated_by = 'DISPATCHER') => request(`/dispatch/dispatch-report/${reportId}`, {
    method: 'POST',
    body: JSON.stringify({ updated_by })
  }),
  getWaitingQueue: () => request('/dispatch/waiting-queue'),
  forceEscalate: (reportId, reason) => request(`/dispatch/escalate/${reportId}`, {
    method: 'POST',
    body: JSON.stringify({ reason })
  }),
  getDispatchLogs: () => request('/dispatch/logs'),

  // Handlers
  getHandlers: () => request('/handlers'),
  getHandler: (id) => request(`/handlers/${id}`),
  updateHandlerAvailability: (id, is_available) => request(`/handlers/${id}/availability`, {
    method: 'PUT',
    body: JSON.stringify({ is_available })
  }),
  updateHandlerCapacity: (id, max_capacity) => request(`/handlers/${id}/capacity`, {
    method: 'PUT',
    body: JSON.stringify({ max_capacity })
  }),
  getHandlerAssignments: (id, status) => {
    const qs = status ? `?status=${status}` : '';
    return request(`/handlers/${id}/assignments${qs}`);
  },
  updateAssignmentStatus: (assignmentId, status, resolution_notes, updated_by) => request(`/handlers/assignments/${assignmentId}/status`, {
    method: 'POST',
    body: JSON.stringify({ status, resolution_notes, updated_by })
  }),

  // Routing
  getRoutingRules: () => request('/routing/rules'),
  updateRoutingRule: (id, data) => request(`/routing/rules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  getZones: () => request('/routing/zones'),

  // Analytics
  getDashboardAnalytics: () => request('/analytics/dashboard'),
  getZoneDistribution: () => request('/analytics/zone-distribution'),
  getCategoryDistribution: () => request('/analytics/category-distribution'),
  getPriorityDistribution: () => request('/analytics/priority-distribution'),
  getHandlerWorkload: () => request('/analytics/handler-workload'),
  getRecentActivity: () => request('/analytics/recent-activity')
};
