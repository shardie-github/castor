'use client'

import { SparklesIcon, ArrowRightIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'

interface InlineUpsellProps {
  title: string
  description: string
  ctaText: string
  ctaLink: string
  feature?: string
  variant?: 'info' | 'success' | 'warning'
}

export function InlineUpsell({
  title,
  description,
  ctaText,
  ctaLink,
  feature,
  variant = 'info',
}: InlineUpsellProps) {
  const variants = {
    info: 'bg-blue-50 border-blue-200 text-blue-900',
    success: 'bg-green-50 border-green-200 text-green-900',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-900',
  }

  return (
    <div className={`rounded-lg border p-4 ${variants[variant]}`}>
      <div className="flex items-start space-x-3">
        <SparklesIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="font-semibold mb-1">{title}</h4>
          <p className="text-sm mb-2">{description}</p>
          {feature && (
            <p className="text-xs opacity-75 mb-2">✨ {feature}</p>
          )}
          <Link
            href={ctaLink}
            className="inline-flex items-center text-sm font-semibold hover:underline"
          >
            {ctaText}
            <ArrowRightIcon className="h-4 w-4 ml-1" />
          </Link>
        </div>
      </div>
    </div>
  )
}
