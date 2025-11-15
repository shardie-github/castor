'use client'

import { use } from 'react'
import { Header } from '@/components/navigation/Header'
import Link from 'next/link'
import {
  ArrowLeftIcon,
  PlayIcon,
  CalendarIcon,
  ChartBarIcon,
  PencilIcon,
  TagIcon,
} from '@heroicons/react/24/outline'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'

interface EpisodeDetailPageProps {
  params: Promise<{ id: string }>
}

// Mock data - replace with API call
const mockEpisode = {
  id: '1',
  title: 'The Future of Podcasting',
  number: 156,
  description:
    'In this episode, we explore the latest trends in podcasting, from AI-powered content creation to new monetization strategies. Join us as we discuss what the future holds for podcasters and listeners alike.',
  publishDate: '2025-01-10',
  duration: 3240,
  downloads: 12500,
  listeners: 9800,
  completionRate: 0.72,
  adSlots: [
    { id: '1', position: 'pre-roll', sponsor: 'TechCorp', status: 'booked', cpm: 30 },
    { id: '2', position: 'mid-roll', sponsor: null, status: 'available', cpm: 35 },
    { id: '3', position: 'post-roll', sponsor: 'StartupXYZ', status: 'booked', cpm: 25 },
  ],
  metrics: {
    timeSeries: [
      { date: '2025-01-10', downloads: 3200, listeners: 2500 },
      { date: '2025-01-11', downloads: 2800, listeners: 2200 },
      { date: '2025-01-12', downloads: 2100, listeners: 1800 },
      { date: '2025-01-13', downloads: 1800, listeners: 1500 },
      { date: '2025-01-14', downloads: 1500, listeners: 1200 },
      { date: '2025-01-15', downloads: 1100, listeners: 800 },
    ],
  },
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

export default function EpisodeDetailPage({ params }: EpisodeDetailPageProps) {
  const { id } = use(params)
  const episode = mockEpisode // In real app, fetch by id

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          {/* Back Button */}
          <Link
            href="/creator/episodes"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Back to Episodes
          </Link>

          {/* Episode Header */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-6">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-sm font-medium text-gray-500">Episode #{episode.number}</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    Published
                  </span>
                </div>
                <h1 className="text-3xl font-bold text-gray-900 mb-3">{episode.title}</h1>
                <p className="text-gray-600 mb-4">{episode.description}</p>
                <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <CalendarIcon className="w-4 h-4" />
                    <span>{new Date(episode.publishDate).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <PlayIcon className="w-4 h-4" />
                    <span>{formatDuration(episode.duration)}</span>
                  </div>
                </div>
              </div>
              <div className="mt-4 md:mt-0 flex items-center space-x-2">
                <button
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center space-x-2"
                  aria-label="Edit episode"
                >
                  <PencilIcon className="w-4 h-4" />
                  <span>Edit</span>
                </button>
                <button
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center space-x-2"
                  aria-label="Play episode"
                >
                  <PlayIcon className="w-4 h-4" />
                  <span>Play</span>
                </button>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-sm text-gray-600 mb-1">Total Downloads</div>
              <div className="text-3xl font-bold text-gray-900">
                {episode.downloads.toLocaleString()}
              </div>
              <div className="text-sm text-green-600 mt-2">+12% from average</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-sm text-gray-600 mb-1">Total Listeners</div>
              <div className="text-3xl font-bold text-gray-900">
                {episode.listeners.toLocaleString()}
              </div>
              <div className="text-sm text-blue-600 mt-2">78% of downloads</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-sm text-gray-600 mb-1">Completion Rate</div>
              <div className="text-3xl font-bold text-gray-900">
                {(episode.completionRate * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-purple-600 mt-2">Above average</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-sm text-gray-600 mb-1">Revenue</div>
              <div className="text-3xl font-bold text-gray-900">
                ${(episode.adSlots.filter((s) => s.status === 'booked').length * 1000).toLocaleString()}
              </div>
              <div className="text-sm text-green-600 mt-2">2 slots booked</div>
            </div>
          </div>

          {/* Performance Chart */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                <ChartBarIcon className="w-5 h-5 mr-2" />
                Performance Over Time
              </h2>
            </div>
            <div className="overflow-x-auto">
              <div className="min-w-[600px]">
                <TimeSeriesChart
                  data={episode.metrics.timeSeries}
                  dataKeys={['downloads', 'listeners']}
                  height={300}
                />
              </div>
            </div>
          </div>

          {/* Ad Slots */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                <TagIcon className="w-5 h-5 mr-2" />
                Ad Slots
              </h2>
              <button
                className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                aria-label="Add ad slot"
              >
                Add Slot
              </button>
            </div>
            <div className="space-y-3">
              {episode.adSlots.map((slot) => (
                <div
                  key={slot.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 capitalize">
                        {slot.position.replace('-', ' ')}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          slot.status === 'booked'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {slot.status}
                      </span>
                    </div>
                    {slot.sponsor ? (
                      <div className="text-sm text-gray-600">Sponsored by {slot.sponsor}</div>
                    ) : (
                      <div className="text-sm text-gray-500">Available for sponsorship</div>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-gray-900">${slot.cpm} CPM</div>
                    {slot.status === 'available' && (
                      <button
                        className="mt-2 px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700"
                        aria-label="Book ad slot"
                      >
                        Book Now
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
