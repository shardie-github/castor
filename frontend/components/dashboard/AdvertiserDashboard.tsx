'use client'

/**
 * DELTA:20251113_064143 Advertiser Dashboard Component
 * 
 * Displays:
 * - Audience Fit Summary
 * - Projected CPM
 * - Inventory Calendar
 */

import { useEffect, useState } from 'react'

interface AdvertiserDashboardProps {
  advertiserId?: string
}

interface Match {
  podcast_id: string
  podcast_title: string
  score: number
  rationale: string
  signals: Record<string, any>
}

interface AudienceFit {
  matches: Match[]
  avg_score: number
  top_score: number
}

interface ProjectedCPM {
  avg_cpm_cents: number
  effective_cpm_cents: number
  projected_cpm_cents: number
}

interface InventoryItem {
  episode_id: string
  episode_title: string
  podcast_title: string
  publish_date: string
  available_slots: number
}

export function AdvertiserDashboard({ advertiserId }: AdvertiserDashboardProps) {
  const [audienceFit, setAudienceFit] = useState<AudienceFit | null>(null)
  const [projectedCPM, setProjectedCPM] = useState<ProjectedCPM | null>(null)
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const params = advertiserId ? `?advertiser_id=${advertiserId}` : ''
        const response = await fetch(`/api/v1/dashboard/advertiser${params}`)
        
        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.statusText}`)
        }
        
        const data = await response.json()
        setAudienceFit(data.audience_fit_summary)
        setProjectedCPM(data.projected_cpm)
        setInventory(data.inventory_calendar)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
        console.error('Advertiser dashboard error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [advertiserId])

  if (loading) {
    return <div className="p-6">Loading advertiser dashboard...</div>
  }

  if (error) {
    return <div className="p-6 text-red-600">Error: {error}</div>
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Advertiser Dashboard</h1>

      {/* Audience Fit Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Audience Fit Summary</h2>
        {audienceFit && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 p-4 rounded">
                <div className="text-sm text-gray-600">Average Score</div>
                <div className="text-2xl font-bold">{audienceFit.avg_score.toFixed(1)}</div>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <div className="text-sm text-gray-600">Top Score</div>
                <div className="text-2xl font-bold">{audienceFit.top_score.toFixed(1)}</div>
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold">Top Matches</h3>
              {audienceFit.matches.slice(0, 5).map((match) => (
                <div key={match.podcast_id} className="border rounded p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-semibold">{match.podcast_title}</div>
                      <div className="text-sm text-gray-600">{match.rationale}</div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${match.score >= 80 ? 'text-green-600' : match.score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {match.score.toFixed(0)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Projected CPM */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Projected CPM</h2>
        {projectedCPM && (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <div className="text-sm text-gray-600">Average CPM</div>
              <div className="text-2xl font-bold">${(projectedCPM.avg_cpm_cents / 100).toFixed(2)}</div>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <div className="text-sm text-gray-600">Effective CPM</div>
              <div className="text-2xl font-bold">${(projectedCPM.effective_cpm_cents / 100).toFixed(2)}</div>
            </div>
            <div className="bg-purple-50 p-4 rounded">
              <div className="text-sm text-gray-600">Projected CPM</div>
              <div className="text-2xl font-bold">${(projectedCPM.projected_cpm_cents / 100).toFixed(2)}</div>
            </div>
          </div>
        )}
      </div>

      {/* Inventory Calendar */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Inventory Calendar (Next 30 Days)</h2>
        {inventory.length === 0 ? (
          <div className="text-gray-500">No available inventory</div>
        ) : (
          <div className="space-y-2">
            {inventory.slice(0, 10).map((item) => (
              <div key={item.episode_id} className="border rounded p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold">{item.episode_title}</div>
                    <div className="text-sm text-gray-600">{item.podcast_title}</div>
                    <div className="text-sm text-gray-500">
                      {new Date(item.publish_date).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-semibold ${item.available_slots > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {item.available_slots} slots
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
