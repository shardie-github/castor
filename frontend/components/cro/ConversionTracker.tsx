'use client'

import { useEffect } from 'react'

interface ConversionTrackerProps {
  eventName: string
  properties?: Record<string, any>
  trigger?: boolean
}

export function ConversionTracker({
  eventName,
  properties = {},
  trigger = true,
}: ConversionTrackerProps) {
  useEffect(() => {
    if (!trigger) return

    // Track conversion event
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', eventName, {
        ...properties,
        event_category: 'conversion',
        event_label: eventName,
      })
    }

    // Track in analytics API
    if (typeof window !== 'undefined' && window.fetch) {
      fetch('/api/v1/analytics/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: 'conversion',
          event_name: eventName,
          properties,
        }),
      }).catch(() => {
        // Silently fail if analytics endpoint is not available
      })
    }
  }, [eventName, properties, trigger])

  return null
}

// Declare gtag for TypeScript
declare global {
  interface Window {
    gtag?: (...args: any[]) => void
  }
}
