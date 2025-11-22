'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'next/navigation'
import { Header } from '@/components/navigation/Header'
import { api } from '@/lib/api'
import { useState } from 'react'

export default function ReportsPage() {
  const params = useParams()
  const campaignId = params.id as string
  const queryClient = useQueryClient()
  const [generatingReportId, setGeneratingReportId] = useState<string | null>(null)

  const { data: reports, isLoading } = useQuery({
    queryKey: ['reports', campaignId],
    queryFn: () => api.getReports(campaignId),
  })

  const generateReportMutation = useMutation({
    mutationFn: (options: any) => api.generateReport(campaignId, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', campaignId] })
      setGeneratingReportId(null)
    },
    onError: () => {
      setGeneratingReportId(null)
    },
  })

  const handleGenerateReport = (format: string) => {
    setGeneratingReportId(format)
    generateReportMutation.mutate({
      report_type: 'sponsor_report',
      format: format,
      include_roi: true,
      include_attribution: true,
    })
  }

  if (isLoading) {
    return (
      <>
        <Header />
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading reports...</p>
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
            <h1 className="text-3xl font-bold text-gray-900">Campaign Reports</h1>
            <p className="text-gray-600 mt-2">Generate and download reports for this campaign</p>
          </div>

          {/* Generate Report Section */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Generate New Report</h2>
            <div className="flex gap-4">
              <button
                onClick={() => handleGenerateReport('pdf')}
                disabled={generatingReportId !== null}
                className={`px-6 py-3 rounded-lg font-medium ${
                  generatingReportId === 'pdf'
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {generatingReportId === 'pdf' ? 'Generating...' : 'Generate PDF Report'}
              </button>
              <button
                onClick={() => handleGenerateReport('csv')}
                disabled={generatingReportId !== null}
                className={`px-6 py-3 rounded-lg font-medium ${
                  generatingReportId === 'csv'
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {generatingReportId === 'csv' ? 'Generating...' : 'Generate CSV Report'}
              </button>
              <button
                onClick={() => handleGenerateReport('excel')}
                disabled={generatingReportId !== null}
                className={`px-6 py-3 rounded-lg font-medium ${
                  generatingReportId === 'excel'
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-purple-600 hover:bg-purple-700 text-white'
                }`}
              >
                {generatingReportId === 'excel' ? 'Generating...' : 'Generate Excel Report'}
              </button>
            </div>
            {generateReportMutation.isError && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
                Failed to generate report. Please try again.
              </div>
            )}
          </div>

          {/* Reports History */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-semibold">Report History</h2>
            </div>
            {reports && reports.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Generated At
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Format
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Size
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reports.map((report: any) => (
                      <tr key={report.report_id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(report.generated_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                            {report.format.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {report.report_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {report.file_size_bytes
                            ? `${(report.file_size_bytes / 1024).toFixed(1)} KB`
                            : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {report.file_url ? (
                            <a
                              href={`/api/v1/reports/${report.report_id}/download`}
                              className="text-blue-600 hover:underline"
                            >
                              Download
                            </a>
                          ) : (
                            <span className="text-gray-400">Processing...</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p>No reports generated yet</p>
                <p className="text-sm mt-2">Generate your first report above</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
