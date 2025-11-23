/**
 * API Client for Castor Backend
 * 
 * Provides typed API methods for frontend components.
 * Handles authentication, error handling, and request/response transformation.
 */

import axios, { AxiosInstance, AxiosError } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Types
export interface Campaign {
  campaign_id: string
  name: string
  status: string
  start_date: string
  end_date: string
  tenant_id?: string
  podcast_id?: string
  sponsor_id?: string
  campaign_value?: number
}

export interface CampaignAnalytics {
  campaign_id: string
  revenue?: number
  conversions?: number
  roi?: number
  impressions?: number
  clicks?: number
}

export interface DashboardAnalytics {
  total_campaigns?: number
  active_campaigns?: number
  total_revenue?: number
  total_conversions?: number
  average_roi?: number
  recent_performance?: Array<{
    campaign_id: string
    name: string
    revenue: number
    conversions: number
    roi: number
  }>
}

export interface Podcast {
  podcast_id: string
  name: string
  rss_feed_url?: string
  tenant_id?: string
}

export interface Episode {
  episode_id: string
  podcast_id: string
  title: string
  published_at?: string
  duration_seconds?: number
}

export interface User {
  user_id: string
  email: string
  name: string
  tenant_id?: string
}

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
      timeout: 30000, // 30 second timeout
    })

    // Request interceptor: Add auth token
    this.client.interceptors.request.use(
      (config) => {
        // Try to get token from localStorage (client-side)
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('access_token')
          if (token) {
            config.headers.Authorization = `Bearer ${token}`
          }
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor: Handle errors
    this.client.interceptors.response.use(
      (response) => response.data,
      (error: AxiosError) => {
        // Handle 401 Unauthorized - redirect to login
        if (error.response?.status === 401) {
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            window.location.href = '/auth/login'
          }
        }

        // Handle 403 Forbidden
        if (error.response?.status === 403) {
          console.error('Access forbidden:', error.response.data)
        }

        // Handle 500+ server errors
        if (error.response?.status && error.response.status >= 500) {
          console.error('Server error:', error.response.data)
        }

        return Promise.reject(error)
      }
    )
  }

  // ==================== Campaigns ====================

  /**
   * Get all campaigns for the current user/tenant
   */
  async getCampaigns(): Promise<Campaign[]> {
    return this.client.get('/api/v1/campaigns')
  }

  /**
   * Get a single campaign by ID
   */
  async getCampaign(campaignId: string): Promise<Campaign> {
    return this.client.get(`/api/v1/campaigns/${campaignId}`)
  }

  /**
   * Create a new campaign
   */
  async createCampaign(data: Partial<Campaign>): Promise<Campaign> {
    return this.client.post('/api/v1/campaigns', data)
  }

  /**
   * Update a campaign
   */
  async updateCampaign(campaignId: string, data: Partial<Campaign>): Promise<Campaign> {
    return this.client.put(`/api/v1/campaigns/${campaignId}`, data)
  }

  /**
   * Delete a campaign
   */
  async deleteCampaign(campaignId: string): Promise<void> {
    return this.client.delete(`/api/v1/campaigns/${campaignId}`)
  }

  /**
   * Get analytics for a specific campaign
   */
  async getCampaignAnalytics(campaignId: string): Promise<CampaignAnalytics> {
    return this.client.get(`/api/v1/campaigns/${campaignId}/analytics`)
  }

  // ==================== Dashboard ====================

  /**
   * Get dashboard analytics
   */
  async getDashboardAnalytics(): Promise<DashboardAnalytics> {
    return this.client.get('/api/v1/dashboard')
  }

  // ==================== Podcasts ====================

  /**
   * Get all podcasts for the current user/tenant
   */
  async getPodcasts(): Promise<Podcast[]> {
    return this.client.get('/api/v1/podcasts')
  }

  /**
   * Get a single podcast by ID
   */
  async getPodcast(podcastId: string): Promise<Podcast> {
    return this.client.get(`/api/v1/podcasts/${podcastId}`)
  }

  /**
   * Create a new podcast
   */
  async createPodcast(data: Partial<Podcast>): Promise<Podcast> {
    return this.client.post('/api/v1/podcasts', data)
  }

  /**
   * Update a podcast
   */
  async updatePodcast(podcastId: string, data: Partial<Podcast>): Promise<Podcast> {
    return this.client.put(`/api/v1/podcasts/${podcastId}`, data)
  }

  // ==================== Episodes ====================

  /**
   * Get episodes for a podcast
   */
  async getEpisodes(podcastId: string): Promise<Episode[]> {
    return this.client.get(`/api/v1/podcasts/${podcastId}/episodes`)
  }

  /**
   * Get a single episode
   */
  async getEpisode(episodeId: string): Promise<Episode> {
    return this.client.get(`/api/v1/episodes/${episodeId}`)
  }

  /**
   * Create a new episode
   */
  async createEpisode(data: Partial<Episode>): Promise<Episode> {
    return this.client.post('/api/v1/episodes', data)
  }

  // ==================== Analytics ====================

  /**
   * Get analytics data
   */
  async getAnalytics(params?: {
    start_date?: string
    end_date?: string
    podcast_id?: string
    episode_id?: string
  }): Promise<any> {
    return this.client.get('/api/v1/analytics', { params })
  }

  // ==================== Reports ====================

  /**
   * Generate a report
   */
  async generateReport(data: {
    report_type: string
    start_date: string
    end_date: string
    campaign_id?: string
  }): Promise<any> {
    return this.client.post('/api/v1/reports', data)
  }

  // ==================== Authentication ====================

  /**
   * Login user
   */
  async login(email: string, password: string): Promise<{
    access_token: string
    refresh_token: string
    token_type: string
    expires_in: number
    user: User
  }> {
    const response = await this.client.post('/api/v1/auth/login', { email, password })
    
    // Store tokens
    if (typeof window !== 'undefined' && response.access_token) {
      localStorage.setItem('access_token', response.access_token)
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token)
      }
    }
    
    return response
  }

  /**
   * Register new user
   */
  async register(data: {
    email: string
    password: string
    name: string
    accept_terms: boolean
    accept_privacy: boolean
  }): Promise<User> {
    return this.client.post('/api/v1/auth/register', data)
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
    return this.client.post('/api/v1/auth/logout')
  }

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<User> {
    return this.client.get('/api/v1/auth/me')
  }

  // ==================== Users ====================

  /**
   * Get user profile
   */
  async getUser(userId: string): Promise<User> {
    return this.client.get(`/api/v1/users/${userId}`)
  }

  /**
   * Update user profile
   */
  async updateUser(userId: string, data: Partial<User>): Promise<User> {
    return this.client.put(`/api/v1/users/${userId}`, data)
  }

  // ==================== Sponsors ====================

  /**
   * Get sponsors
   */
  async getSponsors(): Promise<any[]> {
    return this.client.get('/api/v1/sponsors')
  }

  /**
   * Get a single sponsor
   */
  async getSponsor(sponsorId: string): Promise<any> {
    return this.client.get(`/api/v1/sponsors/${sponsorId}`)
  }

  // ==================== Attribution ====================

  /**
   * Track attribution event
   */
  async trackAttribution(data: {
    event_type: string
    campaign_id: string
    user_id?: string
    properties?: Record<string, any>
  }): Promise<any> {
    return this.client.post('/api/v1/attribution/events', data)
  }

  /**
   * Get attribution data
   */
  async getAttribution(campaignId: string, params?: {
    start_date?: string
    end_date?: string
    attribution_model?: string
  }): Promise<any> {
    return this.client.get(`/api/v1/attribution/campaigns/${campaignId}`, { params })
  }

  // ==================== Admin ====================

  /**
   * Get sprint metrics (admin only)
   */
  async getSprintMetrics(): Promise<any> {
    return this.client.get('/api/v1/sprint-metrics')
  }

  /**
   * Get monitoring data (admin only)
   */
  async getMonitoringData(): Promise<any> {
    return this.client.get('/api/v1/monitoring')
  }
}

// Export singleton instance
export const api = new APIClient()

// Export class for testing
export default APIClient
