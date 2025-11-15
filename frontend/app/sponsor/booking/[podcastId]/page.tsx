'use client'

import { use, useState } from 'react'
import { Header } from '@/components/navigation/Header'
import Link from 'next/link'
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import { CheckCircleIcon as CheckCircleIconSolid } from '@heroicons/react/24/solid'

interface BookingPageProps {
  params: Promise<{ podcastId: string }>
}

// Mock data - replace with API call
const mockPodcast = {
  id: '1',
  title: 'Tech Talk Weekly',
  host: 'Sarah Johnson',
  listeners: 125000,
  cpmRange: [25, 35],
  category: 'Technology',
}

const mockAvailableSlots = [
  { id: '1', episodeTitle: 'The Future of AI', publishDate: '2025-01-20', slots: ['pre-roll', 'mid-roll'] },
  { id: '2', episodeTitle: 'Building Startups', publishDate: '2025-01-27', slots: ['pre-roll', 'mid-roll', 'post-roll'] },
  { id: '3', episodeTitle: 'Tech Trends 2025', publishDate: '2025-02-03', slots: ['mid-roll'] },
]

type BookingStep = 'select-slots' | 'review' | 'payment' | 'confirmation'

export default function BookingPage({ params }: BookingPageProps) {
  const { podcastId } = use(params)
  const [currentStep, setCurrentStep] = useState<BookingStep>('select-slots')
  const [selectedSlots, setSelectedSlots] = useState<Array<{ episodeId: string; position: string }>>([])
  const [selectedEpisodes, setSelectedEpisodes] = useState<Set<string>>(new Set())

  const toggleSlot = (episodeId: string, position: string) => {
    const slotKey = `${episodeId}-${position}`
    setSelectedSlots((prev) => {
      const exists = prev.find((s) => s.episodeId === episodeId && s.position === position)
      if (exists) {
        return prev.filter((s) => !(s.episodeId === episodeId && s.position === position))
      }
      return [...prev, { episodeId, position }]
    })
  }

  const toggleEpisode = (episodeId: string) => {
    setSelectedEpisodes((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(episodeId)) {
        newSet.delete(episodeId)
        setSelectedSlots((slots) => slots.filter((s) => s.episodeId !== episodeId))
      } else {
        newSet.add(episodeId)
      }
      return newSet
    })
  }

  const calculateTotal = () => {
    const baseCPM = 30 // Average CPM
    const estimatedImpressions = mockPodcast.listeners * 0.7 // 70% listen rate
    return selectedSlots.length * (estimatedImpressions / 1000) * baseCPM
  }

  const handleContinue = () => {
    if (currentStep === 'select-slots') {
      if (selectedSlots.length === 0) {
        alert('Please select at least one ad slot')
        return
      }
      setCurrentStep('review')
    } else if (currentStep === 'review') {
      setCurrentStep('payment')
    } else if (currentStep === 'payment') {
      setCurrentStep('confirmation')
    }
  }

  const steps = [
    { id: 'select-slots', name: 'Select Slots', number: 1 },
    { id: 'review', name: 'Review', number: 2 },
    { id: 'payment', name: 'Payment', number: 3 },
    { id: 'confirmation', name: 'Confirmation', number: 4 },
  ]

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
          {/* Back Button */}
          <Link
            href={`/marketplace/${podcastId}`}
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Back to Podcast
          </Link>

          {/* Progress Steps */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
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

          {/* Step 1: Select Slots */}
          {currentStep === 'select-slots' && (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Select Ad Slots</h2>
                <p className="text-gray-600 mb-6">
                  Choose episodes and ad slot positions for your sponsorship
                </p>

                <div className="space-y-4">
                  {mockAvailableSlots.map((episode) => (
                    <div
                      key={episode.id}
                      className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <input
                              type="checkbox"
                              checked={selectedEpisodes.has(episode.id)}
                              onChange={() => toggleEpisode(episode.id)}
                              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                            />
                            <h3 className="font-semibold text-gray-900">{episode.episodeTitle}</h3>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-gray-600 ml-6">
                            <div className="flex items-center space-x-1">
                              <CalendarIcon className="w-4 h-4" />
                              <span>{new Date(episode.publishDate).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      {selectedEpisodes.has(episode.id) && (
                        <div className="ml-6 space-y-2">
                          <div className="text-sm font-medium text-gray-700 mb-2">
                            Select ad positions:
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {episode.slots.map((position) => {
                              const isSelected = selectedSlots.some(
                                (s) => s.episodeId === episode.id && s.position === position
                              )
                              return (
                                <button
                                  key={position}
                                  onClick={() => toggleSlot(episode.id, position)}
                                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    isSelected
                                      ? 'bg-blue-600 text-white'
                                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                  }`}
                                >
                                  {position.replace('-', ' ')}
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Summary Card */}
              <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-blue-600 mb-1">Selected Slots</div>
                    <div className="text-2xl font-bold text-blue-900">
                      {selectedSlots.length} slot{selectedSlots.length !== 1 ? 's' : ''}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-blue-600 mb-1">Estimated Cost</div>
                    <div className="text-2xl font-bold text-blue-900">
                      ${calculateTotal().toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Review */}
          {currentStep === 'review' && (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Review Your Booking</h2>

                <div className="space-y-6">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Podcast</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="font-semibold text-gray-900">{mockPodcast.title}</div>
                      <div className="text-sm text-gray-600 mt-1">Hosted by {mockPodcast.host}</div>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Selected Ad Slots</h3>
                    <div className="space-y-2">
                      {selectedSlots.map((slot, index) => {
                        const episode = mockAvailableSlots.find((e) => e.id === slot.episodeId)
                        return (
                          <div key={index} className="bg-gray-50 rounded-lg p-4 flex items-center justify-between">
                            <div>
                              <div className="font-medium text-gray-900">{episode?.episodeTitle}</div>
                              <div className="text-sm text-gray-600 capitalize">
                                {slot.position.replace('-', ' ')} • {episode?.publishDate}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="font-semibold text-gray-900">${mockPodcast.cpmRange[0]}-${mockPodcast.cpmRange[1]} CPM</div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div className="border-t border-gray-200 pt-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-600">Estimated Impressions</span>
                      <span className="font-semibold text-gray-900">
                        {(mockPodcast.listeners * 0.7 * selectedSlots.length).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-600">CPM Range</span>
                      <span className="font-semibold text-gray-900">
                        ${mockPodcast.cpmRange[0]}-${mockPodcast.cpmRange[1]}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-lg font-bold text-gray-900 pt-4 border-t border-gray-200">
                      <span>Total Estimated Cost</span>
                      <span>${calculateTotal().toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Payment */}
          {currentStep === 'payment' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Payment Information</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Card Number
                  </label>
                  <input
                    type="text"
                    placeholder="1234 5678 9012 3456"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Expiry Date
                    </label>
                    <input
                      type="text"
                      placeholder="MM/YY"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">CVC</label>
                    <input
                      type="text"
                      placeholder="123"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Billing Address
                  </label>
                  <input
                    type="text"
                    placeholder="123 Main St"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-2"
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="text"
                      placeholder="City"
                      className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <input
                      type="text"
                      placeholder="ZIP"
                      className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Confirmation */}
          {currentStep === 'confirmation' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center">
              <CheckCircleIcon className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Booking Confirmed!</h2>
              <p className="text-gray-600 mb-6">
                Your sponsorship booking has been confirmed. You'll receive a confirmation email shortly.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/sponsor/campaigns"
                  className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                >
                  View Campaigns
                </Link>
                <Link
                  href="/marketplace"
                  className="px-6 py-3 bg-white text-blue-600 font-semibold rounded-lg border-2 border-blue-600 hover:bg-blue-50 transition-colors"
                >
                  Browse More Podcasts
                </Link>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          {currentStep !== 'confirmation' && (
            <div className="flex items-center justify-between mt-6">
              <button
                onClick={() => {
                  if (currentStep === 'select-slots') {
                    window.history.back()
                  } else if (currentStep === 'review') {
                    setCurrentStep('select-slots')
                  } else if (currentStep === 'payment') {
                    setCurrentStep('review')
                  }
                }}
                className="px-6 py-3 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors"
              >
                {currentStep === 'select-slots' ? 'Cancel' : 'Back'}
              </button>
              <button
                onClick={handleContinue}
                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
              >
                {currentStep === 'payment' ? 'Complete Booking' : 'Continue'}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
