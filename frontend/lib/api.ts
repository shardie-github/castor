import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Add error handling interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized - redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login'
      }
    }
    
    // Log error for debugging
    console.error('API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.response?.data?.detail || error.message
    })
    
    return Promise.reject(error)
  }
)

export const api = {
  // Dashboard Analytics
  async getDashboardAnalytics() {
    try {
      const { data } = await apiClient.get('/analytics/dashboard')
      return data
    } catch (error: any) {
      // Return null if endpoint doesn't exist yet
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  },

  // Campaigns
  async getCampaigns() {
    const { data } = await apiClient.get('/campaigns')
    return data
  },

  async getCampaign(campaignId: string) {
    const { data } = await apiClient.get(`/campaigns/${campaignId}`)
    return data
  },

  async getCampaignAnalytics(campaignId: string) {
    const { data } = await apiClient.get(`/campaigns/${campaignId}/analytics`)
    return data
  },

  // Sprint Metrics
  async getSprintMetrics(startDate?: string, endDate?: string) {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    const { data } = await apiClient.get(`/sprint-metrics/dashboard?${params.toString()}`)
    return data
  },

  async getTTFVDistribution() {
    const { data } = await apiClient.get('/sprint-metrics/ttfv-distribution')
    return data
  },

  async getCompletionRate(startDate?: string, endDate?: string) {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    const { data } = await apiClient.get(`/sprint-metrics/completion-rate?${params.toString()}`)
    return data
  },

  // Reports
  async generateReport(campaignId: string, options: any) {
    const { data } = await apiClient.post(`/reports/generate`, {
      campaign_id: campaignId,
      ...options,
    })
    return data
  },
}
