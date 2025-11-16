'use client'

import { useState } from 'react'
import { SparklesIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import Link from 'next/link'

interface UpgradePromptProps {
  title: string
  description: string
  ctaText: string
  ctaLink: string
  features?: string[]
  variant?: 'banner' | 'card' | 'inline'
  dismissible?: boolean
  onDismiss?: () => void
}

export function UpgradePrompt({
  title,
  description,
  ctaText,
  ctaLink,
  features = [],
  variant = 'banner',
  dismissible = true,
  onDismiss,
}: UpgradePromptProps) {
  const [isDismissed, setIsDismissed] = useState(false)

  const handleDismiss = () => {
    setIsDismissed(true)
    onDismiss?.()
  }

  if (isDismissed && dismissible) {
    return null
  }

  if (variant === 'banner') {
    return (
      <div className="relative bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-4 shadow-lg">
        {dismissible && (
          <button
            onClick={handleDismiss}
            className="absolute right-4 top-4 text-white/80 hover:text-white"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        )}
        <div className="flex items-center justify-between">
          <div className="flex items-start space-x-3">
            <SparklesIcon className="h-6 w-6 text-white mt-1" />
            <div>
              <h3 className="text-white font-semibold">{title}</h3>
              <p className="text-blue-100 text-sm mt-1">{description}</p>
            </div>
          </div>
          <Link href={ctaLink}>
            <Button variant="secondary" size="sm">
              {ctaText}
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  if (variant === 'card') {
    return (
      <div className="relative bg-white border-2 border-blue-200 rounded-lg p-6 shadow-sm">
        {dismissible && (
          <button
            onClick={handleDismiss}
            className="absolute right-4 top-4 text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        )}
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="h-10 w-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <SparklesIcon className="h-6 w-6 text-white" />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <p className="text-gray-600 text-sm mt-1">{description}</p>
            {features.length > 0 && (
              <ul className="mt-3 space-y-1">
                {features.map((feature, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start">
                    <span className="text-blue-600 mr-2">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>
            )}
            <Link href={ctaLink} className="mt-4 inline-block">
              <Button size="sm">{ctaText}</Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // inline variant
  return (
    <div className="inline-flex items-center space-x-2 text-sm">
      <SparklesIcon className="h-4 w-4 text-blue-600" />
      <span className="text-gray-700">{description}</span>
      <Link href={ctaLink} className="text-blue-600 hover:text-blue-700 font-semibold">
        {ctaText} →
      </Link>
    </div>
  )
}
