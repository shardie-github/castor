'use client'

import React from 'react'
import { clsx } from 'clsx'

interface LoadingStateProps {
  message?: string
  fullScreen?: boolean
  className?: string
}

/**
 * Loading State Component
 * 
 * Displays a loading spinner with optional message.
 */
export function LoadingState({
  message = 'Loading...',
  fullScreen = false,
  className,
}: LoadingStateProps) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center',
        fullScreen ? 'min-h-screen' : 'py-12',
        className
      )}
    >
      <div className="relative">
        <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      </div>
      {message && (
        <p className="mt-4 text-sm text-gray-600">{message}</p>
      )}
    </div>
  )
}
