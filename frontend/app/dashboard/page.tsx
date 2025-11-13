'use client'

import { useQuery } from '@tanstack/react-query'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'
import { HeatmapChart } from '@/components/charts/HeatmapChart'
import { FunnelChartComponent } from '@/components/charts/FunnelChart'
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
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {/* Listener Engagement */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-semibold mb-4">Listener Engagement</h2>
        {listenerEngagement && (
          <TimeSeriesChart
            data={listenerEngagement.timeSeries}
            dataKeys={['listeners', 'downloads', 'streams']}
            height={400}
          />
        )}
      </section>

      {/* Ad Performance */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-semibold mb-4">Ad Performance</h2>
        {adPerformance && (
          <div className="space-y-6">
            <TimeSeriesChart
              data={adPerformance.timeSeries}
              dataKeys={['impressions', 'clicks', 'conversions']}
              height={300}
            />
            {adPerformance.heatmap && (
              <HeatmapChart data={adPerformance.heatmap} height={300} />
            )}
          </div>
        )}
      </section>

      {/* Sponsor ROI */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-semibold mb-4">Sponsor ROI</h2>
        {sponsorROI && (
          <div className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Total ROI</div>
                <div className="text-2xl font-bold">
                  {(sponsorROI.totalROI * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Total Revenue</div>
                <div className="text-2xl font-bold">
                  ${sponsorROI.totalRevenue.toLocaleString()}
                </div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Total Cost</div>
                <div className="text-2xl font-bold">
                  ${sponsorROI.totalCost.toLocaleString()}
                </div>
              </div>
            </div>
            {sponsorROI.funnel && (
              <FunnelChartComponent data={sponsorROI.funnel} height={300} />
            )}
          </div>
        )}
      </section>
    </div>
  )
}
