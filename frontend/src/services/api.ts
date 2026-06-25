import axios, { type AxiosInstance } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

export const api: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Auth interceptor
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Token refresh interceptor
api.interceptors.response.use(
  r => r,
  async error => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refresh = localStorage.getItem('refresh_token')
        if (!refresh) throw new Error('No refresh token')
        const { data } = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, { refresh_token: refresh })
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth
export const authApi = {
  login: (email: string, password: string) => api.post('/auth/login', { email, password }),
  register: (data: any) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  refresh: (refresh_token: string) => api.post('/auth/refresh', { refresh_token }),
  logout: () => api.post('/auth/logout'),
  changePassword: (data: any) => api.post('/auth/change-password', data),
}

// Users
export const usersApi = {
  list: (params?: any) => api.get('/users', { params }),
  get: (id: string) => api.get(`/users/${id}`),
  create: (data: any) => api.post('/users', data),
  update: (id: string, data: any) => api.patch(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
}

// Departments
export const departmentsApi = {
  list: (params?: any) => api.get('/departments', { params }),
  get: (id: string) => api.get(`/departments/${id}`),
  create: (data: any) => api.post('/departments', data),
  update: (id: string, data: any) => api.patch(`/departments/${id}`, data),
  stats: (id: string) => api.get(`/departments/${id}/stats`),
}

// Complaints
export const complaintsApi = {
  list: (params?: any) => api.get('/complaints', { params }),
  get: (id: string) => api.get(`/complaints/${id}`),
  create: (data: any) => api.post('/complaints', data),
  update: (id: string, data: any) => api.patch(`/complaints/${id}`, data),
  history: (id: string) => api.get(`/complaints/${id}/history`),
  feedback: (id: string, data: any) => api.post(`/complaints/${id}/feedback`, data),
  escalate: (id: string) => api.post(`/complaints/${id}/escalate`),
}

// Projects
export const projectsApi = {
  list: (params?: any) => api.get('/projects', { params }),
  get: (id: string) => api.get(`/projects/${id}`),
  create: (data: any) => api.post('/projects', data),
  update: (id: string, data: any) => api.patch(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  atRisk: (threshold?: number) => api.get('/projects/at-risk', { params: { threshold } }),
}

// Analytics
export const analyticsApi = {
  overview: () => api.get('/analytics/overview'),
  complaintsByCategory: () => api.get('/analytics/complaints/by-category'),
  complaintsByStatus: () => api.get('/analytics/complaints/by-status'),
  complaintsByWard: (limit?: number) => api.get('/analytics/complaints/by-ward', { params: { limit } }),
  projectsByStatus: () => api.get('/analytics/projects/by-status'),
  departmentPerformance: () => api.get('/analytics/departments/performance'),
}

// GIS
export const gisApi = {
  complaintPoints: (params?: any) => api.get('/gis/complaints/points', { params }),
  projectPoints: (params?: any) => api.get('/gis/projects/points', { params }),
  heatmap: () => api.get('/gis/heatmap/complaints'),
}

// AI
export const aiApi = {
  triage: (data: any) => api.post('/ai/complaint/triage', data),
  projectRisk: (data: any) => api.post('/ai/project/risk', data),
  wardRisk: () => api.get('/ai/ward-risk'),
  health: () => api.get('/ai/health'),
}

// Forum
export const forumApi = {
  listThreads: (params?: any) => api.get('/forum/threads', { params }),
  getThread: (id: string) => api.get(`/forum/threads/${id}`),
  createThread: (data: any) => api.post('/forum/threads', data),
  listComments: (threadId: string) => api.get(`/forum/threads/${threadId}/comments`),
  addComment: (threadId: string, data: any) => api.post(`/forum/threads/${threadId}/comments`, data),
  pinThread: (id: string) => api.patch(`/forum/threads/${id}/pin`),
}

// Notifications
export const notificationsApi = {
  list: (params?: any) => api.get('/notifications', { params }),
  unreadCount: () => api.get('/notifications/unread-count'),
  markRead: (id: string) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/mark-all-read'),
}
