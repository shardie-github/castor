'use client'

import { useQuery } from '@tanstack/react-query'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'
import { HeatmapChart } from '@/components/charts/HeatmapChart'
import { FunnelChartComponent } from '@/components/charts/FunnelChart'
import { Header } from '@/components/navigation/Header'
import { api } from '@/lib/api'
import { useState, useEffect } from 'react'

export default function DashboardPage() {
  // Get campaigns to show real data
  const { data: campaigns, isLoading: loadingCampaigns } = useQuery({
    queryKey: ['campaigns'],
    queryFn: () => api.getCampaigns(),
  })

  // Get dashboard analytics from real API
  const { data: dashboardAnalytics, isLoading: loadingAnalytics, error: analyticsError } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => api.getDashboardAnalytics(),
    retry: 1, // Don't retry if endpoint doesn't exist yet
  })

  // Calculate metrics from campaigns
  const [campaignMetrics, setCampaignMetrics] = useState({
    totalCampaigns: 0,
    activeCampaigns: 0,
    totalRevenue: 0,
    totalConversions: 0,
    averageROI: 0,
  })

  useEffect(() => {
    if (campaigns && campaigns.length > 0) {
      // Fetch analytics for each campaign
      const fetchCampaignAnalytics = async () => {
        let totalRevenue = 0
        let totalConversions = 0
        let roiSum = 0
        let roiCount = 0
        let activeCount = 0

        for (const campaign of campaigns.slice(0, 10)) {
          try {
            const analytics = await api.getCampaignAnalytics(campaign.campaign_id)
            if (analytics) {
              totalRevenue += analytics.revenue || 0
              totalConversions += analytics.conversions || 0
              if (analytics.roi !== null && analytics.roi !== undefined) {
                roiSum += analytics.roi
                roiCount++
              }
              if (analytics.conversions > 0) {
                activeCount++
              }
            }
          } catch (error) {
            // Skip campaigns with no analytics data
            console.warn(`Failed to fetch analytics for campaign ${campaign.campaign_id}:`, error)
          }
        }

        setCampaignMetrics({
          totalCampaigns: campaigns.length,
          activeCampaigns: activeCount,
          totalRevenue,
          totalConversions,
          averageROI: roiCount > 0 ? roiSum / roiCount : 0,
        })
      }

      fetchCampaignAnalytics()
    } else {
      setCampaignMetrics({
        totalCampaigns: 0,
        activeCampaigns: 0,
        totalRevenue: 0,
        totalConversions: 0,
        averageROI: 0,
      })
    }
  }, [campaigns])

  const isLoading = loadingCampaigns || loadingAnalytics

  if (isLoading) {
    return (
      <>
        <Header />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading dashboard...</p>
          </div>
        </div>
      </>
    )
  }

  // Error handling
  if (analyticsError) {
    console.warn('Dashboard analytics error:', analyticsError)
    // Continue rendering with campaign data only
  }

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-2">Track your podcast performance and sponsorship metrics</p>
          </div>

          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-600 mb-1">Total Campaigns</div>
                <div className="text-3xl font-bold text-gray-900">
                  {campaignMetrics.totalCampaigns}
                </div>
                <div className="text-sm text-gray-500 mt-2">
                  {dashboardAnalytics?.total_campaigns || campaignMetrics.totalCampaigns} total
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-600 mb-1">Active Campaigns</div>
                <div className="text-3xl font-bold text-gray-900">
                  {campaignMetrics.activeCampaigns}
                </div>
                <div className="text-sm text-blue-600 mt-2">
                  {dashboardAnalytics?.active_campaigns || campaignMetrics.activeCampaigns} with conversions
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-600 mb-1">Total Revenue</div>
                <div className="text-3xl font-bold text-gray-900">
                  ${(dashboardAnalytics?.total_revenue || campaignMetrics.totalRevenue).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="text-sm text-purple-600 mt-2">
                  {campaignMetrics.totalConversions} conversions
                </div>
              </div>
            </div>

            {/* Campaign Performance Summary */}
            <section className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Campaign Performance</h2>
              {dashboardAnalytics && dashboardAnalytics.recent_performance && dashboardAnalytics.recent_performance.length > 0 ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Average ROI</div>
                      <div className="text-2xl font-bold text-blue-700">
                        {dashboardAnalytics.average_roi ? `${dashboardAnalytics.average_roi.toFixed(1)}%` : 'N/A'}
                      </div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Total Revenue</div>
                      <div className="text-2xl font-bold text-green-700">
                        ${dashboardAnalytics.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Total Conversions</div>
                      <div className="text-2xl font-bold text-purple-700">
                        {dashboardAnalytics.total_conversions}
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    Showing data for {dashboardAnalytics.recent_performance.length} recent campaigns
                  </div>
                </div>
              ) : campaignMetrics.totalCampaigns > 0 ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Average ROI</div>
                      <div className="text-2xl font-bold text-blue-700">
                        {campaignMetrics.averageROI ? `${campaignMetrics.averageROI.toFixed(1)}%` : 'N/A'}
                      </div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Total Revenue</div>
                      <div className="text-2xl font-bold text-green-700">
                        ${campaignMetrics.totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Total Conversions</div>
                      <div className="text-2xl font-bold text-purple-700">
                        {campaignMetrics.totalConversions}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>No campaign data available</p>
                  <p className="text-sm mt-2">Create your first campaign to see performance metrics here</p>
                </div>
              )}
            </section>

            {/* Campaigns List */}
            {campaigns && campaigns.length > 0 && (
              <section className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Recent Campaigns</h2>
                <div className="space-y-2">
                  {campaigns.slice(0, 5).map((campaign: any) => (
                    <div key={campaign.campaign_id} className="border-b pb-2">
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="font-medium">{campaign.name}</div>
                          <div className="text-sm text-gray-500">
                            {new Date(campaign.start_date).toLocaleDateString()} - {new Date(campaign.end_date).toLocaleDateString()}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium">{campaign.status}</div>
                          <a
                            href={`/campaigns/${campaign.campaign_id}`}
                            className="text-sm text-blue-600 hover:underline"
                          >
                            View Details →
                          </a>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {campaigns.length > 5 && (
                  <div className="mt-4 text-center">
                    <a href="/campaigns" className="text-blue-600 hover:underline">
                      View all {campaigns.length} campaigns →
                    </a>
                  </div>
                )}
              </section>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
