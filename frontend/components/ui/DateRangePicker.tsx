'use client'

import { useState } from 'react'
import { CalendarIcon } from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

interface DateRangePickerProps {
  startDate?: Date
  endDate?: Date
  onChange: (startDate: Date | undefined, endDate: Date | undefined) => void
  className?: string
}

export function DateRangePicker({
  startDate,
  endDate,
  onChange,
  className,
}: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false)

  const formatDate = (date: Date | undefined) => {
    if (!date) return ''
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value ? new Date(e.target.value) : undefined
    onChange(date, endDate)
  }

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value ? new Date(e.target.value) : undefined
    onChange(startDate, date)
  }

  return (
    <div className={clsx('relative', className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <CalendarIcon className="w-5 h-5 text-gray-400" />
        <span className="text-sm text-gray-700">
          {startDate && endDate
            ? `${formatDate(startDate)} - ${formatDate(endDate)}`
            : 'Select date range'}
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={startDate?.toISOString().split('T')[0] || ''}
                onChange={handleStartDateChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={endDate?.toISOString().split('T')[0] || ''}
                onChange={handleEndDateChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => {
                  onChange(undefined, undefined)
                  setIsOpen(false)
                }}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
