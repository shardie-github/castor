'use client'

import { useQuery } from '@tanstack/react-query'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'
import { HeatmapChart } from '@/components/charts/HeatmapChart'
import { FunnelChartComponent } from '@/components/charts/FunnelChart'
import { Header } from '@/components/navigation/Header'
import { api } from '@/lib/api'

export default function DashboardPage() {
  const { data: listenerEngagement, isLoading: loadingEngagement } = useQuery({
    queryKey: ['listener-engagement'],
    queryFn: () => api.getListenerEngagement(),
  })

  const { data: adPerformance, isLoading: loadingAdPerformance } = useQuery({
    queryKey: ['ad-performance'],
    queryFn: () => api.getAdPerformance(),
  })

  const { data: sponsorROI, isLoading: loadingROI } = useQuery({
    queryKey: ['sponsor-roi'],
    queryFn: () => api.getSponsorROI(),
  })

  if (loadingEngagement || loadingAdPerformance || loadingROI) {
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
                <div className="text-sm text-gray-600 mb-1">Total Listeners</div>
                <div className="text-3xl font-bold text-gray-900">
                  {listenerEngagement?.summary?.totalListeners?.toLocaleString() || '0'}
                </div>
                <div className="text-sm text-green-600 mt-2">+12% from last month</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-600 mb-1">Active Sponsorships</div>
                <div className="text-3xl font-bold text-gray-900">
                  {sponsorROI?.activeCampaigns || '0'}
                </div>
                <div className="text-sm text-blue-600 mt-2">3 ending soon</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-600 mb-1">Monthly Revenue</div>
                <div className="text-3xl font-bold text-gray-900">
                  ${sponsorROI?.monthlyRevenue?.toLocaleString() || '0'}
                </div>
                <div className="text-sm text-purple-600 mt-2">On track for goal</div>
              </div>
            </div>

            {/* Listener Engagement */}
            <section className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Listener Engagement</h2>
              {listenerEngagement && listenerEngagement.timeSeries ? (
                <div className="overflow-x-auto">
                  <div className="min-w-[600px]">
                    <TimeSeriesChart
                      data={listenerEngagement.timeSeries}
                      dataKeys={['listeners', 'downloads', 'streams']}
                      height={400}
                    />
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>No listener engagement data available</p>
                  <p className="text-sm mt-2">Start tracking your podcast to see metrics here</p>
                </div>
              )}
            </section>

            {/* Ad Performance */}
            <section className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Ad Performance</h2>
              {adPerformance && adPerformance.timeSeries ? (
                <div className="space-y-6">
                  <div className="overflow-x-auto">
                    <div className="min-w-[600px]">
                      <TimeSeriesChart
                        data={adPerformance.timeSeries}
                        dataKeys={['impressions', 'clicks', 'conversions']}
                        height={300}
                      />
                    </div>
                  </div>
                  {adPerformance.heatmap && (
                    <div className="overflow-x-auto">
                      <div className="min-w-[600px]">
                        <HeatmapChart data={adPerformance.heatmap} height={300} />
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>No ad performance data available</p>
                  <p className="text-sm mt-2">Create a sponsorship campaign to see metrics here</p>
                </div>
              )}
            </section>

            {/* Sponsor ROI */}
            <section className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Sponsor ROI</h2>
              {sponsorROI ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Total ROI</div>
                      <div className="text-2xl font-bold text-blue-700">
                        {(sponsorROI.totalROI * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Total Revenue</div>
                      <div className="text-2xl font-bold text-green-700">
                        ${sponsorROI.totalRevenue.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Total Cost</div>
                      <div className="text-2xl font-bold text-purple-700">
                        ${sponsorROI.totalCost.toLocaleString()}
                      </div>
                    </div>
                  </div>
                  {sponsorROI.funnel && (
                    <div className="overflow-x-auto">
                      <div className="min-w-[400px]">
                        <FunnelChartComponent data={sponsorROI.funnel} height={300} />
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>No ROI data available</p>
                  <p className="text-sm mt-2">Complete a sponsorship campaign to see ROI metrics</p>
                </div>
              )}
            </section>
          </div>
        </div>
      </div>
    </>
  )
}
