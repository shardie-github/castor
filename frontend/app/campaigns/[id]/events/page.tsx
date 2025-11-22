'use client'

import { useQuery } from '@tanstack/react-query'
import { useParams } from 'next/navigation'
import { Header } from '@/components/navigation/Header'
import { api } from '@/lib/api'
import { useState, useEffect } from 'react'

export default function AttributionEventsPage() {
  const params = useParams()
  const campaignId = params.id as string
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data: events, isLoading, error, refetch } = useQuery({
    queryKey: ['attribution-events', campaignId],
    queryFn: () => api.getAttributionEvents(campaignId),
    refetchInterval: autoRefresh ? 5000 : false, // Refresh every 5 seconds if enabled
  })

  useEffect(() => {
    // Auto-refresh when component mounts
    const interval = setInterval(() => {
      if (autoRefresh) {
        refetch()
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [autoRefresh, refetch])

  if (isLoading) {
    return (
      <>
        <Header />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading attribution events...</p>
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
            <p className="text-red-600">Error loading attribution events</p>
            <button
              onClick={() => refetch()}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </>
    )
  }

  const impressions = events?.filter((e: any) => e.event_type === 'impression') || []
  const clicks = events?.filter((e: any) => e.event_type === 'click') || []
  const conversions = events?.filter((e: any) => e.event_type === 'conversion') || []

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8 flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Attribution Events</h1>
              <p className="text-gray-600 mt-2">Track attribution events for this campaign</p>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-600">Auto-refresh</span>
              </label>
              <button
                onClick={() => refetch()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Refresh
              </button>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Impressions</div>
              <div className="text-3xl font-bold text-gray-900">{impressions.length}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Clicks</div>
              <div className="text-3xl font-bold text-gray-900">{clicks.length}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Conversions</div>
              <div className="text-3xl font-bold text-gray-900">{conversions.length}</div>
              <div className="text-sm text-green-600 mt-2">
                ${conversions.reduce((sum: number, e: any) => sum + (e.conversion_value || 0), 0).toFixed(2)} total value
              </div>
            </div>
          </div>

          {/* Events Table */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-semibold">Recent Events</h2>
            </div>
            {events && events.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Timestamp
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Promo Code
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Conversion Value
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Page URL
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {events.map((event: any) => (
                      <tr key={event.event_id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              event.event_type === 'conversion'
                                ? 'bg-green-100 text-green-800'
                                : event.event_type === 'click'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {event.event_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(event.timestamp).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {event.promo_code || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {event.conversion_value ? `$${event.conversion_value.toFixed(2)}` : '-'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          <a
                            href={event.page_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline truncate max-w-xs block"
                          >
                            {event.page_url}
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p>No attribution events yet</p>
                <p className="text-sm mt-2">Events will appear here when the attribution pixel records them</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
