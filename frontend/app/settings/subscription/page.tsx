'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { LoadingState } from '@/components/ui/LoadingState'
import { CheckIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'

interface Subscription {
  subscription_id: string
  status: string
  current_period_start: string
  current_period_end: string
  plan_id: string
  cancel_at_period_end: boolean
}

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'month',
    features: [
      '1 podcast',
      'Basic analytics',
      '1 campaign per month',
      'Basic reports',
      'Community support',
    ],
    price_id: null,
  },
  {
    id: 'starter',
    name: 'Starter',
    price: '$29',
    period: 'month',
    features: [
      '3 podcasts',
      'Advanced analytics',
      'Unlimited campaigns',
      'Automated reports',
      'ROI calculations',
      'Email support',
    ],
    price_id: 'price_starter',
  },
  {
    id: 'professional',
    name: 'Professional',
    price: '$99',
    period: 'month',
    features: [
      '10 podcasts',
      'All Starter features',
      'API access',
      'White-label reports',
      'Advanced attribution',
      'Priority support',
    ],
    price_id: 'price_professional',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    features: [
      'Unlimited podcasts',
      'All Professional features',
      'Team collaboration',
      'SSO/SAML',
      'Dedicated account manager',
      'Custom integrations',
    ],
    price_id: 'price_enterprise',
  },
]

export default function SubscriptionPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [currentTier, setCurrentTier] = useState('free')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isUpgrading, setIsUpgrading] = useState(false)

  useEffect(() => {
    loadSubscription()
  }, [])

  const loadSubscription = async () => {
    setIsLoading(true)
    setError('')

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('Not authenticated')
      }

      // Get user info to determine current tier
      const userResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (userResponse.ok) {
        const userData = await userResponse.json()
        setCurrentTier(userData.subscription_tier || 'free')
      }

      // Get subscription details
      try {
        const subResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/billing/subscription`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })

        if (subResponse.ok) {
          const subData = await subResponse.json()
          setSubscription(subData)
        }
      } catch (err) {
        // No subscription found, that's okay
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load subscription')
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpgrade = async (planId: string, priceId: string | null) => {
    if (!priceId) {
      alert('Please contact sales for Enterprise pricing')
      return
    }

    setIsUpgrading(true)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/billing/subscribe`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ price_id: priceId }),
      })

      const data = await response.json()

      if (response.ok) {
        alert('Subscription created! Redirecting to payment...')
        // In production, redirect to Stripe Checkout
        loadSubscription()
      } else {
        alert(data.detail || 'Failed to create subscription')
      }
    } catch (err: any) {
      alert(err.message || 'Failed to upgrade')
    } finally {
      setIsUpgrading(false)
    }
  }

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will lose access at the end of the billing period.')) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/billing/subscription/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cancel_immediately: false }),
      })

      if (response.ok) {
        alert('Subscription cancelled. You will retain access until the end of your billing period.')
        loadSubscription()
      } else {
        const data = await response.json()
        alert(data.detail || 'Failed to cancel subscription')
      }
    } catch (err: any) {
      alert(err.message || 'Failed to cancel subscription')
    }
  }

  if (isLoading) {
    return <LoadingState message="Loading subscription..." />
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Subscription</h1>
        <p className="text-gray-600">
          Manage your subscription and billing preferences
        </p>
      </div>

      {subscription && (
        <Card className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Current Subscription</h2>
              <p className="text-gray-600">
                {PLANS.find(p => p.id === currentTier)?.name || currentTier} Plan
              </p>
              {subscription.cancel_at_period_end && (
                <p className="text-sm text-yellow-600 mt-2">
                  Subscription will cancel on {new Date(subscription.current_period_end).toLocaleDateString()}
                </p>
              )}
            </div>
            {!subscription.cancel_at_period_end && (
              <Button variant="danger" onClick={handleCancel}>
                Cancel Subscription
              </Button>
            )}
          </div>
        </Card>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {PLANS.map((plan) => {
          const isCurrentPlan = plan.id === currentTier
          const isHigherTier = ['free', 'starter', 'professional', 'enterprise'].indexOf(plan.id) >
            ['free', 'starter', 'professional', 'enterprise'].indexOf(currentTier)

          return (
            <Card
              key={plan.id}
              className={`relative ${isCurrentPlan ? 'ring-2 ring-blue-600' : ''}`}
            >
              {isCurrentPlan && (
                <div className="absolute top-4 right-4">
                  <span className="bg-blue-600 text-white text-xs font-semibold px-2 py-1 rounded">
                    Current
                  </span>
                </div>
              )}
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                <div className="mt-2">
                  <span className="text-3xl font-bold text-gray-900">{plan.price}</span>
                  {plan.period && (
                    <span className="text-gray-600">/{plan.period}</span>
                  )}
                </div>
              </div>
              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <CheckIcon className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
              <Button
                variant={isCurrentPlan ? 'secondary' : 'primary'}
                className="w-full"
                disabled={isCurrentPlan || isUpgrading}
                onClick={() => handleUpgrade(plan.id, plan.price_id)}
              >
                {isCurrentPlan
                  ? 'Current Plan'
                  : isHigherTier
                  ? 'Upgrade'
                  : plan.id === 'enterprise'
                  ? 'Contact Sales'
                  : 'Select Plan'}
              </Button>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
