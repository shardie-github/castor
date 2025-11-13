'use client'

/**
 * DELTA:20251113_064143 Creator Dashboard Component
 * 
 * Displays:
 * - Pacing vs Flight
 * - Sponsor Revenue
 * - Makegoods Pending
 */

import { useEffect, useState } from 'react'
import { TimeSeriesChart } from '../charts/TimeSeriesChart'

interface CreatorDashboardProps {
  podcastId?: string
}

interface PacingData {
  ios: Array<{
    io_id: string
    flight_start: string
    flight_end: string
    booked_impressions: number
    actual_impressions: number
    flight_progress_pct: number
    pacing_pct: number
  }>
  summary: {
    total_booked: number
    total_delivered: number
    avg_pacing: number
  }
}

interface RevenueData {
  daily: Array<{
    day: string
    revenue: number
  }>
  total_30d: number
  trend: 'up' | 'down'
}

interface Makegood {
  io_id: string
  campaign_id: string
  flight_end: string
  booked_impressions: number
  actual_impressions: number
  shortfall: number
}

export function CreatorDashboard({ podcastId }: CreatorDashboardProps) {
  const [pacing, setPacing] = useState<PacingData | null>(null)
  const [revenue, setRevenue] = useState<RevenueData | null>(null)
  const [makegoods, setMakegoods] = useState<Makegood[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const params = podcastId ? `?podcast_id=${podcastId}` : ''
        const response = await fetch(`/api/v1/dashboard/creator${params}`)
        
        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.statusText}`)
        }
        
        const data = await response.json()
        setPacing(data.pacing_vs_flight)
        setRevenue(data.sponsor_revenue)
        setMakegoods(data.makegoods_pending)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
        console.error('Creator dashboard error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [podcastId])

  if (loading) {
    return <div className="p-6">Loading creator dashboard...</div>
  }

  if (error) {
    return <div className="p-6 text-red-600">Error: {error}</div>
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Creator Dashboard</h1>

      {/* Pacing vs Flight */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Pacing vs Flight</h2>
        {pacing && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded">
                <div className="text-sm text-gray-600">Total Booked</div>
                <div className="text-2xl font-bold">{pacing.summary.total_booked.toLocaleString()}</div>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <div className="text-sm text-gray-600">Total Delivered</div>
                <div className="text-2xl font-bold">{pacing.summary.total_delivered.toLocaleString()}</div>
              </div>
              <div className="bg-purple-50 p-4 rounded">
                <div className="text-sm text-gray-600">Avg Pacing</div>
                <div className="text-2xl font-bold">{pacing.summary.avg_pacing.toFixed(1)}%</div>
              </div>
            </div>
            <div className="space-y-2">
              {pacing.ios.slice(0, 5).map((io) => (
                <div key={io.io_id} className="border rounded p-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">IO {io.io_id.slice(0, 8)}</span>
                    <span className={`text-sm font-semibold ${io.pacing_pct >= 100 ? 'text-green-600' : 'text-yellow-600'}`}>
                      {io.pacing_pct.toFixed(1)}% paced
                    </span>
                  </div>
                  <div className="mt-2 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${Math.min(io.pacing_pct, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Sponsor Revenue */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Sponsor Revenue (30 days)</h2>
        {revenue && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold">${(revenue.total_30d / 100).toFixed(2)}</div>
                <div className={`text-sm ${revenue.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                  Trend: {revenue.trend}
                </div>
              </div>
            </div>
            {revenue.daily.length > 0 && (
              <TimeSeriesChart
                data={revenue.daily.map(d => ({ date: d.day, revenue: d.revenue / 100 }))}
                dataKeys={['revenue']}
                xAxisKey="date"
                height={300}
              />
            )}
          </div>
        )}
      </div>

      {/* Makegoods Pending */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Makegoods Pending</h2>
        {makegoods.length === 0 ? (
          <div className="text-gray-500">No makegoods pending</div>
        ) : (
          <div className="space-y-3">
            {makegoods.map((mg) => (
              <div key={mg.io_id} className="border rounded p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold">IO {mg.io_id.slice(0, 8)}</div>
                    <div className="text-sm text-gray-600">Flight ended: {new Date(mg.flight_end).toLocaleDateString()}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-red-600 font-semibold">-{mg.shortfall.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">impressions short</div>
                  </div>
                </div>
                <div className="mt-2 text-sm">
                  Booked: {mg.booked_impressions.toLocaleString()} | 
                  Delivered: {mg.actual_impressions.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
