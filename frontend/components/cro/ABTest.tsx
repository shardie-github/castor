'use client'

import { ReactNode, useEffect, useState } from 'react'

interface ABTestProps {
  testName: string
  variantA: ReactNode
  variantB: ReactNode
  defaultVariant?: 'A' | 'B'
  onVariantSelect?: (variant: 'A' | 'B') => void
}

export function ABTest({
  testName,
  variantA,
  variantB,
  defaultVariant = 'A',
  onVariantSelect,
}: ABTestProps) {
  const [variant, setVariant] = useState<'A' | 'B'>(defaultVariant)

  useEffect(() => {
    // Get or set variant from localStorage (persistent across sessions)
    const storageKey = `ab_test_${testName}`
    const storedVariant = localStorage.getItem(storageKey) as 'A' | 'B' | null

    if (storedVariant && (storedVariant === 'A' || storedVariant === 'B')) {
      setVariant(storedVariant)
    } else {
      // Randomly assign variant (50/50 split)
      const newVariant = Math.random() < 0.5 ? 'A' : 'B'
      setVariant(newVariant)
      localStorage.setItem(storageKey, newVariant)
    }

    // Track variant assignment
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'ab_test_assignment', {
        test_name: testName,
        variant: variant,
        event_category: 'ab_test',
      })
    }

    onVariantSelect?.(variant)
  }, [testName, onVariantSelect, variant])

  return <>{variant === 'A' ? variantA : variantB}</>
}
