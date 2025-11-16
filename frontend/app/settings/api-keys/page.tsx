'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/navigation/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { FeatureGate } from '@/components/cta/FeatureGate'
import { UpgradePrompt } from '@/components/cta/UpgradePrompt'
import {
  KeyIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  ClipboardIcon,
} from '@heroicons/react/24/outline'

export default function APIKeysPage() {
  const [apiKeys, setApiKeys] = useState<any[]>([])
  const [showKey, setShowKey] = useState<Record<string, boolean>>({})
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

    // Fetch API keys
    fetch('/api/v1/security/api-keys')
      .then((res) => res.json())
      .then((data) => setApiKeys(data))
      .catch(() => {})
  }, [])

  const handleCreateKey = () => {
    // Create new API key
    fetch('/api/v1/security/api-keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: `API Key ${Date.now()}` }),
    })
      .then((res) => res.json())
      .then((data) => {
        setApiKeys([...apiKeys, data])
      })
      .catch(() => {})
  }

  const handleDeleteKey = (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key?')) return

    fetch(`/api/v1/security/api-keys/${keyId}`, {
      method: 'DELETE',
    })
      .then(() => {
        setApiKeys(apiKeys.filter((key) => key.key_id !== keyId))
      })
      .catch(() => {})
  }

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    // Show toast notification
  }

  const toggleShowKey = (keyId: string) => {
    setShowKey({ ...showKey, [keyId]: !showKey[keyId] })
  }

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">API Keys</h1>
            <p className="text-gray-600 mt-2">Manage your API keys for programmatic access</p>
          </div>

          {!hasAccess && (
            <div className="mb-6">
              <UpgradePrompt
                title="API Access Requires Professional Plan"
                description="Upgrade to Professional or Enterprise to access API keys and programmatic access."
                ctaText="Upgrade Now"
                ctaLink="/settings/subscription"
                features={['REST API access', 'Webhook support', 'Rate limit: 10,000 requests/day', 'Priority support']}
                variant="banner"
              />
            </div>
          )}

          <FeatureGate
            hasAccess={hasAccess}
            featureName="API Keys"
            requiredPlan="Professional"
            upgradeLink="/settings/subscription"
            description="API keys allow you to programmatically access your data and integrate with other tools."
          >
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Your API Keys</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Use these keys to authenticate API requests. Keep them secure and never share them publicly.
                  </p>
                </div>
                <Button onClick={handleCreateKey}>
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Create Key
                </Button>
              </div>

              {apiKeys.length === 0 ? (
                <div className="text-center py-12">
                  <KeyIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">No API keys yet</p>
                  <Button onClick={handleCreateKey}>Create Your First API Key</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {apiKeys.map((key) => (
                    <div
                      key={key.key_id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <KeyIcon className="h-5 w-5 text-gray-400" />
                          <span className="font-medium text-gray-900">{key.name || 'Untitled Key'}</span>
                          {key.last_used && (
                            <span className="text-xs text-gray-500">
                              Last used: {new Date(key.last_used).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono">
                            {showKey[key.key_id] ? key.api_key : '•'.repeat(40)}
                          </code>
                          <button
                            onClick={() => toggleShowKey(key.key_id)}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            {showKey[key.key_id] ? (
                              <EyeSlashIcon className="h-4 w-4" />
                            ) : (
                              <EyeIcon className="h-4 w-4" />
                            )}
                          </button>
                          <button
                            onClick={() => handleCopyKey(key.api_key)}
                            className="text-gray-400 hover:text-gray-600"
                            title="Copy to clipboard"
                          >
                            <ClipboardIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteKey(key.key_id)}
                        className="text-red-600 hover:text-red-700 ml-4"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Security Tip:</strong> Never commit API keys to version control. Use environment variables
                  instead.
                </p>
              </div>
            </Card>
          </FeatureGate>
        </div>
      </div>
    </>
  )
}
