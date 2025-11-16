'use client'

import { useState } from 'react'
import { Header } from '@/components/navigation/Header'
import { Button } from '@/components/ui/Button'
import { UpgradePrompt } from '@/components/cta/UpgradePrompt'
import {
  BookOpenIcon,
  CodeBracketIcon,
  RocketLaunchIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'

export default function DocsPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const categories = [
    {
      name: 'Getting Started',
      icon: RocketLaunchIcon,
      docs: [
        { title: 'Quick Start Guide', description: 'Get up and running in 5 minutes' },
        { title: 'Account Setup', description: 'Configure your account and preferences' },
        { title: 'First Campaign', description: 'Create your first campaign' },
      ],
    },
    {
      name: 'API Reference',
      icon: CodeBracketIcon,
      docs: [
        { title: 'Authentication', description: 'Learn how to authenticate API requests' },
        { title: 'Campaigns API', description: 'Manage campaigns programmatically' },
        { title: 'Analytics API', description: 'Retrieve analytics data' },
        { title: 'Webhooks', description: 'Set up webhook notifications' },
      ],
    },
    {
      name: 'Guides',
      icon: BookOpenIcon,
      docs: [
        { title: 'ROI Tracking', description: 'Track return on investment for campaigns' },
        { title: 'Attribution Models', description: 'Understand different attribution methods' },
        { title: 'Report Generation', description: 'Create and customize reports' },
        { title: 'Integrations', description: 'Connect with third-party tools' },
      ],
    },
  ]

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-50 via-white to-purple-50 pt-20 pb-12">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
            <BookOpenIcon className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Documentation</h1>
            <p className="text-xl text-gray-600 mb-8">
              Everything you need to know about using our platform
            </p>

            {/* Search */}
            <div className="relative max-w-2xl mx-auto">
              <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documentation..."
                className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </section>

        {/* Documentation Categories */}
        <section className="py-12">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-3 gap-8">
              {categories.map((category) => {
                const Icon = category.icon
                return (
                  <div key={category.name} className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Icon className="h-6 w-6 text-blue-600" />
                      </div>
                      <h2 className="text-xl font-semibold text-gray-900">{category.name}</h2>
                    </div>
                    <ul className="space-y-3">
                      {category.docs.map((doc, index) => (
                        <li key={index}>
                          <a
                            href={`/docs/${category.name.toLowerCase().replace(' ', '-')}/${doc.title.toLowerCase().replace(' ', '-')}`}
                            className="block p-3 rounded-lg hover:bg-gray-50 transition-colors"
                          >
                            <h3 className="font-medium text-gray-900">{doc.title}</h3>
                            <p className="text-sm text-gray-600 mt-1">{doc.description}</p>
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        {/* API Quick Start */}
        <section className="py-12 bg-white">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            <div className="bg-gray-900 rounded-lg p-8">
              <h2 className="text-2xl font-bold text-white mb-4">API Quick Start</h2>
              <p className="text-gray-300 mb-6">
                Get started with our API in minutes. All API requests require authentication.
              </p>
              <div className="bg-gray-800 rounded-lg p-4 mb-6">
                <pre className="text-green-400 text-sm overflow-x-auto">
                  <code>{`curl https://api.example.com/v1/campaigns \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"`}</code>
                </pre>
              </div>
              <div className="flex space-x-4">
                <Button variant="secondary" href="/docs/api-reference">
                  View Full API Docs
                </Button>
                <Button variant="ghost" className="text-white border-white">
                  Get API Key
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Upgrade Prompt */}
        <section className="py-12">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            <UpgradePrompt
              title="Need More Help?"
              description="Upgrade to Professional for priority support and dedicated documentation assistance."
              ctaText="Upgrade Now"
              ctaLink="/settings/subscription"
              variant="card"
            />
          </div>
        </section>
      </div>
    </>
  )
}
