'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/navigation/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { UpgradePrompt } from '@/components/cta/UpgradePrompt'
import { UpsellModal } from '@/components/cta/UpsellModal'
import { ConversionTracker } from '@/components/cro/ConversionTracker'
import {
  UserCircleIcon,
  EnvelopeIcon,
  CalendarIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'

export default function ProfilePage() {
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    subscriptionTier: 'free',
    createdAt: '',
  })
  const [showUpsellModal, setShowUpsellModal] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Fetch user profile
    fetch('/api/v1/users/me')
      .then((res) => res.json())
      .then((data) => {
        setProfile(data)
        setIsLoading(false)
      })
      .catch(() => setIsLoading(false))
  }, [])

  const handleUpgradeClick = () => {
    setShowUpsellModal(true)
  }

  const isFreeTier = profile.subscriptionTier === 'free'
  const isProTier = profile.subscriptionTier === 'professional' || profile.subscriptionTier === 'enterprise'

  return (
    <>
      <ConversionTracker eventName="profile_page_view" />
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
          {/* Upgrade Prompt for Free Users */}
          {isFreeTier && (
            <div className="mb-6">
              <UpgradePrompt
                title="Unlock Premium Features"
                description="Upgrade to Professional to access advanced analytics, unlimited campaigns, and priority support."
                ctaText="Upgrade Now"
                ctaLink="/settings/subscription"
                features={[
                  'Advanced analytics & insights',
                  'Unlimited campaigns',
                  'Priority support',
                  'White-label reports',
                ]}
                variant="banner"
              />
            </div>
          )}

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
            <p className="text-gray-600 mt-2">Manage your account settings and preferences</p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Profile Information Card */}
            <Card className="p-6">
              <div className="flex items-center space-x-4 mb-6">
                <div className="h-16 w-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <UserCircleIcon className="h-10 w-10 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">{profile.name || 'Loading...'}</h2>
                  <p className="text-sm text-gray-600">{profile.email || 'Loading...'}</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between py-2 border-b border-gray-200">
                  <div className="flex items-center space-x-2">
                    <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                    <span className="text-sm text-gray-600">Email</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{profile.email || 'Loading...'}</span>
                </div>

                <div className="flex items-center justify-between py-2 border-b border-gray-200">
                  <div className="flex items-center space-x-2">
                    <CalendarIcon className="h-5 w-5 text-gray-400" />
                    <span className="text-sm text-gray-600">Member Since</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {profile.createdAt ? new Date(profile.createdAt).toLocaleDateString() : 'Loading...'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-2">
                  <div className="flex items-center space-x-2">
                    <ShieldCheckIcon className="h-5 w-5 text-gray-400" />
                    <span className="text-sm text-gray-600">Plan</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900 capitalize">{profile.subscriptionTier}</span>
                </div>
              </div>

              <div className="mt-6">
                <Button variant="secondary" className="w-full">
                  Edit Profile
                </Button>
              </div>
            </Card>

            {/* Subscription Card with Upsell */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Subscription</h3>
                {isFreeTier && (
                  <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
                    Free Plan
                  </span>
                )}
              </div>

              {isFreeTier ? (
                <div className="space-y-4">
                  <p className="text-sm text-gray-600">
                    You're currently on the free plan. Upgrade to unlock premium features and grow your podcast business faster.
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="text-green-500 mr-2">✓</span>
                      <span>Basic analytics</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="text-green-500 mr-2">✓</span>
                      <span>Up to 3 campaigns</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-400">
                      <span className="text-gray-300 mr-2">✗</span>
                      <span>Advanced analytics</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-400">
                      <span className="text-gray-300 mr-2">✗</span>
                      <span>Unlimited campaigns</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-400">
                      <span className="text-gray-300 mr-2">✗</span>
                      <span>Priority support</span>
                    </div>
                  </div>
                  <Button onClick={handleUpgradeClick} className="w-full" size="lg">
                    <SparklesIcon className="h-5 w-5 mr-2" />
                    Upgrade to Professional
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="rounded-lg bg-green-50 p-4 border border-green-200">
                    <p className="text-sm font-semibold text-green-900">
                      ✓ {profile.subscriptionTier.charAt(0).toUpperCase() + profile.subscriptionTier.slice(1)} Plan Active
                    </p>
                    <p className="text-xs text-green-700 mt-1">You have access to all premium features</p>
                  </div>
                  {!isProTier && (
                    <Button variant="secondary" className="w-full" onClick={handleUpgradeClick}>
                      Upgrade to Enterprise
                    </Button>
                  )}
                </div>
              )}
            </Card>

            {/* Usage Statistics */}
            <Card className="p-6 md:col-span-2">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Statistics</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">0</p>
                  <p className="text-sm text-gray-600 mt-1">Campaigns</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">0</p>
                  <p className="text-sm text-gray-600 mt-1">Podcasts</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">0</p>
                  <p className="text-sm text-gray-600 mt-1">Reports</p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Upsell Modal */}
      <UpsellModal
        isOpen={showUpsellModal}
        onClose={() => setShowUpsellModal(false)}
        title="Upgrade to Professional"
        description="Unlock advanced features to grow your podcast business faster"
        features={[
          'Unlimited campaigns and podcasts',
          'Advanced analytics and insights',
          'White-label reports',
          'Priority email support',
          'API access',
          'Custom integrations',
        ]}
        ctaText="Upgrade Now"
        ctaLink="/settings/subscription"
        currentPlan="Free"
        upgradePlan="Professional"
        price="$99/month"
        highlightFeature="Get 20% off your first month with code UPGRADE20"
      />
    </>
  )
}
