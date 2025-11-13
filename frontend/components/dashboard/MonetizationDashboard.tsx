'use client'

/**
 * DELTA:20251113_064143 Monetization Dashboard Component
 * 
 * Displays:
 * - AI Token Balance & Usage
 * - API Usage Summary
 * - Affiliate Stats
 * - Agency Performance
 * - Revenue Overview
 */

import { useEffect, useState } from 'react'
import { TimeSeriesChart } from '../charts/TimeSeriesChart'

interface MonetizationDashboardProps {}

interface TokenBalance {
  tokens_purchased: number
  tokens_used: number
  tokens_remaining: number
}

interface APIUsageSummary {
  total_calls: number
  successful_calls: number
  failed_calls: number
  total_cost_cents: number
  avg_response_time_ms: number
}

interface AffiliateStats {
  affiliate_id: string
  name: string
  referral_code: string
  total_referrals: number
  total_commission_cents: number
  converted_count: number
}

export function MonetizationDashboard({}: MonetizationDashboardProps) {
  const [tokenBalance, setTokenBalance] = useState<TokenBalance | null>(null)
  const [apiUsage, setApiUsage] = useState<APIUsageSummary | null>(null)
  const [affiliates, setAffiliates] = useState<AffiliateStats[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        
        // Fetch token balance
        const tokenResponse = await fetch('/api/v1/monetization/ai-tokens/balance')
        if (tokenResponse.ok) {
          const tokenData = await tokenResponse.json()
          setTokenBalance(tokenData)
        }
        
        // Fetch API usage
        const apiResponse = await fetch('/api/v1/monetization/api-usage/summary')
        if (apiResponse.ok) {
          const apiData = await apiResponse.json()
          setApiUsage(apiData)
        }
        
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
        console.error('Monetization dashboard error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return <div className="p-6">Loading monetization dashboard...</div>
  }

  if (error) {
    return <div className="p-6 text-red-600">Error: {error}</div>
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Monetization Dashboard</h1>

      {/* AI Token Balance */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">AI Token Balance</h2>
        {tokenBalance && (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <div className="text-sm text-gray-600">Purchased</div>
              <div className="text-2xl font-bold">{tokenBalance.tokens_purchased.toLocaleString()}</div>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <div className="text-sm text-gray-600">Used</div>
              <div className="text-2xl font-bold">{tokenBalance.tokens_used.toLocaleString()}</div>
            </div>
            <div className="bg-purple-50 p-4 rounded">
              <div className="text-sm text-gray-600">Remaining</div>
              <div className="text-2xl font-bold">{tokenBalance.tokens_remaining.toLocaleString()}</div>
            </div>
          </div>
        )}
      </div>

      {/* API Usage */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">API Usage Summary</h2>
        {apiUsage && (
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded">
                <div className="text-sm text-gray-600">Total Calls</div>
                <div className="text-2xl font-bold">{apiUsage.total_calls.toLocaleString()}</div>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <div className="text-sm text-gray-600">Successful</div>
                <div className="text-2xl font-bold">{apiUsage.successful_calls.toLocaleString()}</div>
              </div>
              <div className="bg-red-50 p-4 rounded">
                <div className="text-sm text-gray-600">Failed</div>
                <div className="text-2xl font-bold">{apiUsage.failed_calls.toLocaleString()}</div>
              </div>
              <div className="bg-purple-50 p-4 rounded">
                <div className="text-sm text-gray-600">Cost</div>
                <div className="text-2xl font-bold">${(apiUsage.total_cost_cents / 100).toFixed(2)}</div>
              </div>
            </div>
            <div className="text-sm text-gray-600">
              Avg Response Time: {apiUsage.avg_response_time_ms.toFixed(0)}ms
            </div>
          </div>
        )}
      </div>

      {/* Affiliate Stats */}
      {affiliates.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Affiliate Performance</h2>
          <div className="space-y-2">
            {affiliates.map((affiliate) => (
              <div key={affiliate.affiliate_id} className="border rounded p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold">{affiliate.name}</div>
                    <div className="text-sm text-gray-600">Code: {affiliate.referral_code}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{affiliate.total_referrals} referrals</div>
                    <div className="text-sm text-gray-600">
                      ${(affiliate.total_commission_cents / 100).toFixed(2)} commission
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
