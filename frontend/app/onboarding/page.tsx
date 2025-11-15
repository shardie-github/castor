'use client'

import { useState } from 'react'
import { Header } from '@/components/navigation/Header'
import { useRouter } from 'next/navigation'
import {
  CheckCircleIcon,
  MicrophoneIcon,
  ChartBarIcon,
  LinkIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'
import { CheckCircleIcon as CheckCircleIconSolid } from '@heroicons/react/24/solid'

type OnboardingStep = 'welcome' | 'podcast' | 'integrations' | 'complete'

export default function OnboardingPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome')
  const [podcastData, setPodcastData] = useState({
    title: '',
    description: '',
    rssFeed: '',
    category: '',
  })
  const [integrations, setIntegrations] = useState<string[]>([])

  const steps = [
    { id: 'welcome', name: 'Welcome', number: 1 },
    { id: 'podcast', name: 'Podcast Setup', number: 2 },
    { id: 'integrations', name: 'Integrations', number: 3 },
    { id: 'complete', name: 'Complete', number: 4 },
  ]

  const handleContinue = () => {
    if (currentStep === 'welcome') {
      setCurrentStep('podcast')
    } else if (currentStep === 'podcast') {
      if (!podcastData.title || !podcastData.rssFeed) {
        alert('Please fill in all required fields')
        return
      }
      setCurrentStep('integrations')
    } else if (currentStep === 'integrations') {
      setCurrentStep('complete')
    } else {
      router.push('/dashboard')
    }
  }

  const toggleIntegration = (id: string) => {
    setIntegrations((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-8">
          {/* Progress Steps */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                        steps.findIndex((s) => s.id === currentStep) >= index
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      {steps.findIndex((s) => s.id === currentStep) > index ? (
                        <CheckCircleIconSolid className="w-6 h-6" />
                      ) : (
                        step.number
                      )}
                    </div>
                    <span
                      className={`mt-2 text-xs font-medium ${
                        steps.findIndex((s) => s.id === currentStep) >= index
                          ? 'text-blue-600'
                          : 'text-gray-500'
                      }`}
                    >
                      {step.name}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`h-0.5 flex-1 mx-2 ${
                        steps.findIndex((s) => s.id === currentStep) > index
                          ? 'bg-blue-600'
                          : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Step 1: Welcome */}
          {currentStep === 'welcome' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <MicrophoneIcon className="w-8 h-8 text-blue-600" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to Castor!</h1>
              <p className="text-lg text-gray-600 mb-8">
                Let's get your podcast set up in just a few steps. This will only take a couple of minutes.
              </p>
              <div className="grid md:grid-cols-3 gap-4 mb-8 text-left">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <ChartBarIcon className="w-8 h-8 text-blue-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Track Analytics</h3>
                  <p className="text-sm text-gray-600">
                    Monitor listener growth, engagement, and performance metrics
                  </p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <MicrophoneIcon className="w-8 h-8 text-green-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Manage Episodes</h3>
                  <p className="text-sm text-gray-600">
                    Organize your episodes and assign ad slots for sponsorships
                  </p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <LinkIcon className="w-8 h-8 text-purple-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Connect Integrations</h3>
                  <p className="text-sm text-gray-600">
                    Link your website, hosting platform, and other tools
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Podcast Setup */}
          {currentStep === 'podcast' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Podcast Information</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Podcast Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={podcastData.title}
                    onChange={(e) => setPodcastData({ ...podcastData, title: e.target.value })}
                    placeholder="My Awesome Podcast"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                    aria-required="true"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={podcastData.description}
                    onChange={(e) => setPodcastData({ ...podcastData, description: e.target.value })}
                    placeholder="Tell us about your podcast..."
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    RSS Feed URL <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="url"
                    value={podcastData.rssFeed}
                    onChange={(e) => setPodcastData({ ...podcastData, rssFeed: e.target.value })}
                    placeholder="https://example.com/feed.xml"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                    aria-required="true"
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    We'll automatically sync your episodes from your RSS feed
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <select
                    value={podcastData.category}
                    onChange={(e) => setPodcastData({ ...podcastData, category: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select a category</option>
                    <option value="technology">Technology</option>
                    <option value="business">Business</option>
                    <option value="health">Health</option>
                    <option value="entertainment">Entertainment</option>
                    <option value="education">Education</option>
                    <option value="sports">Sports</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Integrations */}
          {currentStep === 'integrations' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Connect Integrations</h2>
              <p className="text-gray-600 mb-6">
                Link your existing tools (optional - you can add these later)
              </p>
              <div className="space-y-3">
                {[
                  { id: 'shopify', name: 'Shopify', description: 'Sell merch and products' },
                  { id: 'wordpress', name: 'WordPress', description: 'Embed player on your site' },
                  { id: 'wix', name: 'Wix', description: 'Add podcast to your website' },
                  { id: 'godaddy', name: 'GoDaddy', description: 'Website integration' },
                ].map((integration) => (
                  <button
                    key={integration.id}
                    onClick={() => toggleIntegration(integration.id)}
                    className={`w-full p-4 border-2 rounded-lg text-left transition-colors ${
                      integrations.includes(integration.id)
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-gray-900">{integration.name}</div>
                        <div className="text-sm text-gray-600">{integration.description}</div>
                      </div>
                      {integrations.includes(integration.id) && (
                        <CheckIcon className="w-6 h-6 text-blue-600" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 4: Complete */}
          {currentStep === 'complete' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <CheckCircleIcon className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h1 className="text-3xl font-bold text-gray-900 mb-4">You're All Set!</h1>
              <p className="text-lg text-gray-600 mb-8">
                Your podcast has been set up successfully. We're syncing your episodes now, which may
                take a few minutes.
              </p>
              <div className="bg-blue-50 rounded-lg p-6 mb-8 text-left">
                <h3 className="font-semibold text-gray-900 mb-2">What's Next?</h3>
                <ul className="space-y-2 text-gray-700">
                  <li className="flex items-start">
                    <CheckIcon className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Review your dashboard to see analytics</span>
                  </li>
                  <li className="flex items-start">
                    <CheckIcon className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Set up your first sponsorship campaign</span>
                  </li>
                  <li className="flex items-start">
                    <CheckIcon className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Explore the marketplace to find sponsors</span>
                  </li>
                </ul>
              </div>
            </div>
          )}

          {/* Navigation */}
          {currentStep !== 'complete' && (
            <div className="flex items-center justify-between mt-8">
              <button
                onClick={() => {
                  if (currentStep === 'welcome') {
                    router.push('/dashboard')
                  } else if (currentStep === 'podcast') {
                    setCurrentStep('welcome')
                  } else {
                    setCurrentStep('podcast')
                  }
                }}
                className="px-6 py-3 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors"
              >
                {currentStep === 'welcome' ? 'Skip' : 'Back'}
              </button>
              <button
                onClick={handleContinue}
                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
              >
                Continue
              </button>
            </div>
          )}

          {currentStep === 'complete' && (
            <div className="flex justify-center mt-8">
              <button
                onClick={() => router.push('/dashboard')}
                className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
              >
                Go to Dashboard
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
