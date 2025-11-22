'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useState } from 'react'

export function MonitoringDashboard() {
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('24h')

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['monitoring-metrics', timeRange],
    queryFn: () => api.getMonitoringMetrics(timeRange),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading monitoring data...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex justify-end">
        <div className="inline-flex rounded-md shadow-sm">
          {(['1h', '24h', '7d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 text-sm font-medium ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              } border border-gray-300 ${
                range === '1h' ? 'rounded-l-md' : ''
              } ${
                range === '7d' ? 'rounded-r-md' : ''
              }`}
            >
              {range === '1h' ? '1 Hour' : range === '24h' ? '24 Hours' : '7 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* System Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">API Error Rate</div>
          <div className="text-3xl font-bold text-gray-900">
            {metrics?.error_rate ? `${(metrics.error_rate * 100).toFixed(2)}%` : '0%'}
          </div>
          <div className={`text-sm mt-2 ${
            metrics?.error_rate && metrics.error_rate > 0.01 ? 'text-red-600' : 'text-green-600'
          }`}>
            {metrics?.error_rate && metrics.error_rate > 0.01 ? '⚠️ Above threshold' : '✓ Healthy'}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Avg Response Time</div>
          <div className="text-3xl font-bold text-gray-900">
            {metrics?.avg_response_time ? `${metrics.avg_response_time.toFixed(0)}ms` : '0ms'}
          </div>
          <div className={`text-sm mt-2 ${
            metrics?.avg_response_time && metrics.avg_response_time > 2000 ? 'text-red-600' : 'text-green-600'
          }`}>
            {metrics?.avg_response_time && metrics.avg_response_time > 2000 ? '⚠️ Slow' : '✓ Fast'}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Requests/min</div>
          <div className="text-3xl font-bold text-gray-900">
            {metrics?.requests_per_minute || 0}
          </div>
          <div className="text-sm text-gray-500 mt-2">
            {metrics?.total_requests || 0} total
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Active Users</div>
          <div className="text-3xl font-bold text-gray-900">
            {metrics?.active_users || 0}
          </div>
          <div className="text-sm text-gray-500 mt-2">
            Last {timeRange}
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Performance Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-gray-600">P50 Response Time</div>
            <div className="text-2xl font-bold">{metrics?.p50_response_time || 0}ms</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">P95 Response Time</div>
            <div className="text-2xl font-bold">{metrics?.p95_response_time || 0}ms</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">P99 Response Time</div>
            <div className="text-2xl font-bold">{metrics?.p99_response_time || 0}ms</div>
          </div>
        </div>
      </div>

      {/* Error Breakdown */}
      {metrics?.error_breakdown && Object.keys(metrics.error_breakdown).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Error Breakdown</h2>
          <div className="space-y-2">
            {Object.entries(metrics.error_breakdown).map(([error_type, count]) => (
              <div key={error_type} className="flex justify-between items-center">
                <span className="text-sm text-gray-700">{error_type}</span>
                <span className="text-sm font-semibold text-red-600">{count as number}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
