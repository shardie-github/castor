'use client'

import { useState } from 'react'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import { Button } from './Button'
import { clsx } from 'clsx'

interface ExportButtonProps {
  onExport: (format: 'csv' | 'excel' | 'pdf' | 'json') => Promise<void>
  formats?: ('csv' | 'excel' | 'pdf' | 'json')[]
  className?: string
}

export function ExportButton({
  onExport,
  formats = ['csv', 'excel', 'pdf'],
  className,
}: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [showMenu, setShowMenu] = useState(false)

  const handleExport = async (format: 'csv' | 'excel' | 'pdf' | 'json') => {
    setIsExporting(true)
    setShowMenu(false)
    try {
      await onExport(format)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  if (formats.length === 1) {
    return (
      <Button
        onClick={() => handleExport(formats[0])}
        isLoading={isExporting}
        className={className}
      >
        <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
        Export {formats[0].toUpperCase()}
      </Button>
    )
  }

  return (
    <div className={clsx('relative', className)}>
      <Button
        onClick={() => setShowMenu(!showMenu)}
        isLoading={isExporting}
      >
        <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
        Export
      </Button>

      {showMenu && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />
          <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
            <div className="py-1">
              {formats.map((format) => (
                <button
                  key={format}
                  onClick={() => handleExport(format)}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
                >
                  Export as {format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
