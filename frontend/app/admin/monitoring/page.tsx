'use client'

import { Header } from '@/components/navigation/Header'
import { MonitoringDashboard } from '@/components/charts/MonitoringDashboard'

export default function MonitoringPage() {
  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">System Monitoring</h1>
            <p className="text-gray-600 mt-2">Real-time system health and performance metrics</p>
          </div>
          <MonitoringDashboard />
        </div>
      </div>
    </>
  )
}
