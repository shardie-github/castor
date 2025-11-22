'use client'

import { useQuery } from '@tanstack/react-query'
import { useParams } from 'next/navigation'
import { Header } from '@/components/navigation/Header'
import { api } from '@/lib/api'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'

export default function CampaignAnalyticsPage() {
  const params = useParams()
  const campaignId = params.id as string

  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['campaign-analytics', campaignId],
    queryFn: () => api.getCampaignAnalytics(campaignId),
  })

  const { data: campaign } = useQuery({
    queryKey: ['campaign', campaignId],
    queryFn: () => api.getCampaign(campaignId),
  })

  if (isLoading) {
    return (
      <>
        <Header />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading analytics...</p>
          </div>
        </div>
      </>
    )
  }

  if (error) {
    return (
      <>
        <Header />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-600">Error loading analytics</p>
            <p className="text-sm text-gray-500 mt-2">Please try again later</p>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">
              Analytics: {campaign?.name || 'Campaign'}
            </h1>
            <p className="text-gray-600 mt-2">Campaign performance metrics and attribution data</p>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Impressions</div>
              <div className="text-3xl font-bold text-gray-900">
                {analytics?.impressions?.toLocaleString() || '0'}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Clicks</div>
              <div className="text-3xl font-bold text-gray-900">
                {analytics?.clicks?.toLocaleString() || '0'}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Conversions</div>
              <div className="text-3xl font-bold text-gray-900">
                {analytics?.conversions?.toLocaleString() || '0'}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Revenue</div>
              <div className="text-3xl font-bold text-gray-900">
                ${analytics?.revenue?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </div>
            </div>
          </div>

          {/* ROI Card */}
          {analytics?.roi !== null && analytics?.roi !== undefined && (
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">ROI Metrics</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600">ROI</div>
                  <div className="text-2xl font-bold text-blue-700">
                    {analytics.roi.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600">Revenue</div>
                  <div className="text-2xl font-bold text-green-700">
                    ${analytics.revenue?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                  </div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600">Campaign Cost</div>
                  <div className="text-2xl font-bold text-purple-700">
                    ${campaign?.campaign_value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Performance Metrics</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-gray-600">Total Downloads</div>
                <div className="text-xl font-bold">{analytics?.total_downloads || 0}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Total Streams</div>
                <div className="text-xl font-bold">{analytics?.total_streams || 0}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Total Listeners</div>
                <div className="text-xl font-bold">{analytics?.total_listeners || 0}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Attribution Events</div>
                <div className="text-xl font-bold">{analytics?.attribution_events || 0}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
