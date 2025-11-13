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

export const api = {
  // Listener Engagement
  async getListenerEngagement() {
    const { data } = await apiClient.get('/analytics/listener-engagement')
    return data
  },

  // Ad Performance
  async getAdPerformance() {
    const { data } = await apiClient.get('/analytics/ad-performance')
    return data
  },

  // Sponsor ROI
  async getSponsorROI() {
    const { data } = await apiClient.get('/analytics/sponsor-roi')
    return data
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

  // Reports
  async generateReport(campaignId: string, options: any) {
    const { data } = await apiClient.post(`/reports/generate`, {
      campaign_id: campaignId,
      ...options,
    })
    return data
  },
}
