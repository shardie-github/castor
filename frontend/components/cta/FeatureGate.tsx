'use client'

import { ReactNode } from 'react'
import { LockClosedIcon } from '@heroicons/react/24/outline'
import { UpgradePrompt } from './UpgradePrompt'

interface FeatureGateProps {
  children: ReactNode
  hasAccess: boolean
  featureName: string
  requiredPlan: string
  upgradeLink: string
  description?: string
}

export function FeatureGate({
  children,
  hasAccess,
  featureName,
  requiredPlan,
  upgradeLink,
  description,
}: FeatureGateProps) {
  if (hasAccess) {
    return <>{children}</>
  }

  return (
    <div className="relative">
      <div className="blur-sm pointer-events-none select-none">
        {children}
      </div>
      <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm rounded-lg">
        <div className="text-center p-8 max-w-md">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gray-100 mb-4">
            <LockClosedIcon className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {featureName} is a {requiredPlan} feature
          </h3>
          {description && (
            <p className="text-sm text-gray-600 mb-6">{description}</p>
          )}
          <UpgradePrompt
            title={`Upgrade to ${requiredPlan}`}
            description={`Unlock ${featureName} and more premium features`}
            ctaText="Upgrade Now"
            ctaLink={upgradeLink}
            variant="card"
            dismissible={false}
          />
        </div>
      </div>
    </div>
  )
}
