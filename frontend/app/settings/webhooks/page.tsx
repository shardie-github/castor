'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/navigation/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { FeatureGate } from '@/components/cta/FeatureGate'
import { UpgradePrompt } from '@/components/cta/UpgradePrompt'
import {
  LinkIcon,
  PlusIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<any[]>([])
  const [hasAccess, setHasAccess] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check subscription tier
    fetch('/api/v1/users/me')
      .then((res) => res.json())
      .then((data) => {
        setHasAccess(data.subscriptionTier !== 'free')
        setIsLoading(false)
      })
      .catch(() => setIsLoading(false))

    // Fetch webhooks
    fetch('/api/v1/webhooks')
      .then((res) => res.json())
      .then((data) => setWebhooks(data))
      .catch(() => {})
  }, [])

  const handleCreateWebhook = () => {
    // Create new webhook
    const url = prompt('Enter webhook URL:')
    if (!url) return

    fetch('/api/v1/webhooks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        events: ['campaign.created', 'campaign.updated'],
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setWebhooks([...webhooks, data])
      })
      .catch(() => {})
  }

  const handleDeleteWebhook = (webhookId: string) => {
    if (!confirm('Are you sure you want to delete this webhook?')) return

    fetch(`/api/v1/webhooks/${webhookId}`, {
      method: 'DELETE',
    })
      .then(() => {
        setWebhooks(webhooks.filter((webhook) => webhook.webhook_id !== webhookId))
      })
      .catch(() => {})
  }

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Webhooks</h1>
            <p className="text-gray-600 mt-2">Configure webhooks to receive real-time notifications</p>
          </div>

          {!hasAccess && (
            <div className="mb-6">
              <UpgradePrompt
                title="Webhooks Require Professional Plan"
                description="Upgrade to Professional or Enterprise to configure webhooks and receive real-time notifications."
                ctaText="Upgrade Now"
                ctaLink="/settings/subscription"
                features={[
                  'Real-time event notifications',
                  'Custom webhook URLs',
                  'Event filtering',
                  'Retry logic',
                ]}
                variant="banner"
              />
            </div>
          )}

          <FeatureGate
            hasAccess={hasAccess}
            featureName="Webhooks"
            requiredPlan="Professional"
            upgradeLink="/settings/subscription"
            description="Webhooks allow you to receive real-time notifications when events occur in your account."
          >
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Your Webhooks</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Configure webhooks to receive notifications about events in your account.
                  </p>
                </div>
                <Button onClick={handleCreateWebhook}>
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add Webhook
                </Button>
              </div>

              {webhooks.length === 0 ? (
                <div className="text-center py-12">
                  <LinkIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">No webhooks configured</p>
                  <Button onClick={handleCreateWebhook}>Create Your First Webhook</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {webhooks.map((webhook) => (
                    <div
                      key={webhook.webhook_id}
                      className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <LinkIcon className="h-5 w-5 text-gray-400" />
                            <span className="font-medium text-gray-900">{webhook.url}</span>
                            {webhook.is_active ? (
                              <CheckCircleIcon className="h-5 w-5 text-green-500" />
                            ) : (
                              <XCircleIcon className="h-5 w-5 text-red-500" />
                            )}
                          </div>
                          <div className="text-sm text-gray-600 space-y-1">
                            <p>Events: {webhook.events?.join(', ') || 'None'}</p>
                            {webhook.last_triggered && (
                              <p>Last triggered: {new Date(webhook.last_triggered).toLocaleString()}</p>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteWebhook(webhook.webhook_id)}
                          className="text-red-600 hover:text-red-700 ml-4"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Available Events:</strong> campaign.created, campaign.updated, campaign.completed,
                  report.generated, payment.received
                </p>
              </div>
            </Card>
          </FeatureGate>
        </div>
      </div>
    </>
  )
}
