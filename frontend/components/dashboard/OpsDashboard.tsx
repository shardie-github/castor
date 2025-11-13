'use client'

/**
 * DELTA:20251113_064143 Ops Dashboard Component
 * 
 * Displays:
 * - Pipeline Forecast
 * - Win/Loss Analysis
 * - ETL Health
 */

import { useEffect, useState } from 'react'
import { FunnelChartComponent } from '../charts/FunnelChart'

interface OpsDashboardProps {}

interface PipelineStage {
  stage: string
  count: number
  total_value: number
}

interface PipelineForecast {
  stages: PipelineStage[]
  total_deals: number
  total_pipeline_value: number
}

interface WinLoss {
  won: number
  lost: number
  win_rate: number
  total_closed: number
}

interface ETLImport {
  import_id: string
  source: string
  file_name: string
  status: string
  records_imported: number
  records_failed: number
  started_at: string
  completed_at: string | null
  error_message: string | null
}

interface ETLHealth {
  recent_imports: ETLImport[]
  health_status: 'healthy' | 'degraded' | 'unhealthy'
  last_import: string | null
}

export function OpsDashboard({}: OpsDashboardProps) {
  const [pipeline, setPipeline] = useState<PipelineForecast | null>(null)
  const [winLoss, setWinLoss] = useState<WinLoss | null>(null)
  const [etlHealth, setEtlHealth] = useState<ETLHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const response = await fetch('/api/v1/dashboard/ops')
        
        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.statusText}`)
        }
        
        const data = await response.json()
        setPipeline(data.pipeline_forecast)
        setWinLoss(data.win_loss)
        setEtlHealth(data.etl_health)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
        console.error('Ops dashboard error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return <div className="p-6">Loading ops dashboard...</div>
  }

  if (error) {
    return <div className="p-6 text-red-600">Error: {error}</div>
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Operations Dashboard</h1>

      {/* Pipeline Forecast */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Deal Pipeline Forecast</h2>
        {pipeline && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 p-4 rounded">
                <div className="text-sm text-gray-600">Total Deals</div>
                <div className="text-2xl font-bold">{pipeline.total_deals}</div>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <div className="text-sm text-gray-600">Pipeline Value</div>
                <div className="text-2xl font-bold">${pipeline.total_pipeline_value.toLocaleString()}</div>
              </div>
            </div>
            {pipeline.stages.length > 0 && (
              <FunnelChartComponent
                data={pipeline.stages.map(s => ({
                  name: s.stage,
                  value: s.count
                }))}
                height={300}
              />
            )}
            <div className="space-y-2">
              {pipeline.stages.map((stage) => (
                <div key={stage.stage} className="flex justify-between items-center border-b pb-2">
                  <span className="capitalize">{stage.stage}</span>
                  <div className="text-right">
                    <div className="font-semibold">{stage.count} deals</div>
                    <div className="text-sm text-gray-600">${stage.total_value.toLocaleString()}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Win/Loss */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Win/Loss Analysis</h2>
        {winLoss && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-green-50 p-4 rounded">
                <div className="text-sm text-gray-600">Won</div>
                <div className="text-2xl font-bold">{winLoss.won}</div>
              </div>
              <div className="bg-red-50 p-4 rounded">
                <div className="text-sm text-gray-600">Lost</div>
                <div className="text-2xl font-bold">{winLoss.lost}</div>
              </div>
              <div className="bg-blue-50 p-4 rounded">
                <div className="text-sm text-gray-600">Win Rate</div>
                <div className="text-2xl font-bold">{winLoss.win_rate.toFixed(1)}%</div>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span>Won</span>
                <span>{winLoss.won}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-green-600 h-4 rounded-full"
                  style={{ width: `${winLoss.win_rate}%` }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ETL Health */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">ETL Health</h2>
        {etlHealth && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-lg">Status</span>
              <span className={`px-3 py-1 rounded text-sm font-semibold ${
                etlHealth.health_status === 'healthy' ? 'bg-green-100 text-green-800' :
                etlHealth.health_status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {etlHealth.health_status.toUpperCase()}
              </span>
            </div>
            {etlHealth.last_import && (
              <div className="text-sm text-gray-600">
                Last import: {new Date(etlHealth.last_import).toLocaleString()}
              </div>
            )}
            <div className="space-y-2">
              <h3 className="font-semibold">Recent Imports</h3>
              {etlHealth.recent_imports.length === 0 ? (
                <div className="text-gray-500">No recent imports</div>
              ) : (
                etlHealth.recent_imports.slice(0, 5).map((imp) => (
                  <div key={imp.import_id} className="border rounded p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-semibold">{imp.file_name}</div>
                        <div className="text-sm text-gray-600">{imp.source}</div>
                        <div className="text-sm text-gray-500">
                          {new Date(imp.started_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm font-semibold ${
                          imp.status === 'completed' ? 'text-green-600' :
                          imp.status === 'failed' ? 'text-red-600' :
                          'text-yellow-600'
                        }`}>
                          {imp.status}
                        </div>
                        <div className="text-sm text-gray-600">
                          {imp.records_imported} imported
                          {imp.records_failed > 0 && `, ${imp.records_failed} failed`}
                        </div>
                      </div>
                    </div>
                    {imp.error_message && (
                      <div className="mt-2 text-sm text-red-600">{imp.error_message}</div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
