'use client'

import { ReactNode } from 'react'

interface IllustrationProps {
  children: ReactNode
  className?: string
}

export function Illustration({ children, className = '' }: IllustrationProps) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <svg
        viewBox="0 0 400 300"
        className="w-full h-auto"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {children}
      </svg>
    </div>
  )
}

// Common illustration components
export function EmptyStateIllustration() {
  return (
    <Illustration>
      <circle cx="200" cy="150" r="80" fill="#E5E7EB" opacity="0.5" />
      <path
        d="M150 150 L200 120 L250 150 L200 180 Z"
        fill="#9CA3AF"
        opacity="0.7"
      />
      <circle cx="200" cy="150" r="20" fill="#6B7280" />
    </Illustration>
  )
}

export function SuccessIllustration() {
  return (
    <Illustration>
      <circle cx="200" cy="150" r="80" fill="#10B981" opacity="0.2" />
      <path
        d="M170 150 L190 170 L230 130"
        stroke="#10B981"
        strokeWidth="8"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </Illustration>
  )
}

export function GrowthIllustration() {
  return (
    <Illustration>
      <path
        d="M50 250 L100 200 L150 180 L200 150 L250 120 L300 100 L350 80"
        stroke="#3B82F6"
        strokeWidth="4"
        fill="none"
      />
      <circle cx="50" cy="250" r="6" fill="#3B82F6" />
      <circle cx="100" cy="200" r="6" fill="#3B82F6" />
      <circle cx="150" cy="180" r="6" fill="#3B82F6" />
      <circle cx="200" cy="150" r="6" fill="#3B82F6" />
      <circle cx="250" cy="120" r="6" fill="#3B82F6" />
      <circle cx="300" cy="100" r="6" fill="#3B82F6" />
      <circle cx="350" cy="80" r="6" fill="#3B82F6" />
    </Illustration>
  )
}
