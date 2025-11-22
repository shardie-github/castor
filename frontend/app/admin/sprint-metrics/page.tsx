'use client'

import { useQuery } from '@tanstack/react-query'
import { Header } from '@/components/navigation/Header'
import { api } from '@/lib/api'

export default function SprintMetricsPage() {
  const { data: sprintMetrics, isLoading, error } = useQuery({
    queryKey: ['sprint-metrics'],
    queryFn: () => api.getSprintMetrics(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <>
        <Header />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading sprint metrics...</p>
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
            <p className="text-red-600">Error loading sprint metrics</p>
            <p className="text-sm text-gray-500 mt-2">Please check your permissions</p>
          </div>
        </div>
      </>
    )
  }

  const ttfv = sprintMetrics?.ttfv_distribution
  const completion = sprintMetrics?.completion_rate

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Sprint Metrics Dashboard</h1>
            <p className="text-gray-600 mt-2">Track sprint success metrics: TTFV and completion rate</p>
            <p className="text-sm text-gray-500 mt-1">
              Last updated: {sprintMetrics?.timestamp ? new Date(sprintMetrics.timestamp).toLocaleString() : 'N/A'}
            </p>
          </div>

          <div className="space-y-6">
            {/* TTFV Distribution */}
            <section className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Time to First Value (TTFV) Distribution</h2>
              {ttfv && ttfv.count > 0 ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">P50 (Median)</div>
                      <div className="text-2xl font-bold text-blue-700">
                        {ttfv.p50 ? `${(ttfv.p50 / 60).toFixed(1)} min` : 'N/A'}
                      </div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">P75</div>
                      <div className="text-2xl font-bold text-green-700">
                        {ttfv.p75 ? `${(ttfv.p75 / 60).toFixed(1)} min` : 'N/A'}
                      </div>
                    </div>
                    <div className="bg-yellow-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">P90</div>
                      <div className="text-2xl font-bold text-yellow-700">
                        {ttfv.p90 ? `${(ttfv.p90 / 60).toFixed(1)} min` : 'N/A'}
                      </div>
                    </div>
                    <div className="bg-red-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">P95</div>
                      <div className="text-2xl font-bold text-red-700">
                        {ttfv.p95 ? `${(ttfv.p95 / 60).toFixed(1)} min` : 'N/A'}
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Mean</div>
                      <div className="text-xl font-bold text-gray-900">
                        {ttfv.mean ? `${(ttfv.mean / 60).toFixed(1)} min` : 'N/A'}
                      </div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Sample Size</div>
                      <div className="text-xl font-bold text-gray-900">{ttfv.count} users</div>
                    </div>
                  </div>
                  {/* Simple histogram visualization */}
                  <div className="mt-4">
                    <div className="text-sm text-gray-600 mb-2">Target: &lt;15 minutes for 80% of users</div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-blue-600 h-4 rounded-full"
                        style={{
                          width: ttfv.p90 && ttfv.p90 < 900
                            ? '100%'
                            : ttfv.p75 && ttfv.p75 < 900
                            ? '75%'
                            : ttfv.p50 && ttfv.p50 < 900
                            ? '50%'
                            : '25%',
                        }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {ttfv.p90 && ttfv.p90 < 900
                        ? '✓ Target met (P90 < 15 min)'
                        : ttfv.p75 && ttfv.p75 < 900
                        ? '⚠ Close to target (P75 < 15 min)'
                        : '✗ Target not met'}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>No TTFV data available</p>
                  <p className="text-sm mt-2">TTFV is calculated when users create their first campaign</p>
                </div>
              )}
            </section>

            {/* Completion Rate */}
            <section className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Campaign Completion Rate</h2>
              {completion ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Completion Rate</div>
                      <div className="text-3xl font-bold text-blue-700">
                        {completion.completion_rate.toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Completed Campaigns</div>
                      <div className="text-2xl font-bold text-green-700">
                        {completion.completed_campaigns}
                      </div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Total Campaigns</div>
                      <div className="text-2xl font-bold text-gray-900">
                        {completion.total_campaigns}
                      </div>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="mt-4">
                    <div className="text-sm text-gray-600 mb-2">Target: &gt;70% completion rate</div>
                    <div className="w-full bg-gray-200 rounded-full h-6">
                      <div
                        className={`h-6 rounded-full flex items-center justify-center text-white text-sm font-semibold ${
                          completion.completion_rate >= 70
                            ? 'bg-green-600'
                            : completion.completion_rate >= 50
                            ? 'bg-yellow-600'
                            : 'bg-red-600'
                        }`}
                        style={{ width: `${Math.min(completion.completion_rate, 100)}%` }}
                      >
                        {completion.completion_rate.toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {completion.completion_rate >= 70
                        ? '✓ Target met'
                        : completion.completion_rate >= 50
                        ? '⚠ Below target'
                        : '✗ Significantly below target'}
                    </div>
                  </div>
                  {completion.start_date && (
                    <div className="text-sm text-gray-500 mt-2">
                      Period: {new Date(completion.start_date).toLocaleDateString()} -{' '}
                      {completion.end_date
                        ? new Date(completion.end_date).toLocaleDateString()
                        : 'Present'}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p>No completion rate data available</p>
                  <p className="text-sm mt-2">Completion rate is calculated when campaigns generate reports</p>
                </div>
              )}
            </section>

            {/* Error Rate (if available) */}
            {sprintMetrics?.error_rate !== null && sprintMetrics?.error_rate !== undefined && (
              <section className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Error Rate</h2>
                <div className="space-y-4">
                  <div className="bg-red-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-600">Current Error Rate</div>
                    <div className="text-3xl font-bold text-red-700">
                      {sprintMetrics.error_rate.toFixed(2)}%
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 mb-2">Target: &lt;2% error rate</div>
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div
                      className={`h-4 rounded-full ${
                        sprintMetrics.error_rate < 2
                          ? 'bg-green-600'
                          : sprintMetrics.error_rate < 5
                          ? 'bg-yellow-600'
                          : 'bg-red-600'
                      }`}
                      style={{ width: `${Math.min(sprintMetrics.error_rate * 10, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
