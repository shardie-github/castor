'use client'

import { use } from 'react'
import { Header } from '@/components/navigation/Header'
import Link from 'next/link'
import {
  ArrowLeftIcon,
  StarIcon,
  UserGroupIcon,
  ChartBarIcon,
  CalendarIcon,
  TagIcon,
  CheckBadgeIcon,
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'
import { PodcastPlayer } from '@/components/player/PodcastPlayer'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'

interface PodcastDetailPageProps {
  params: Promise<{ id: string }>
}

// Mock data - replace with API call
const mockPodcast = {
  id: '1',
  title: 'Tech Talk Weekly',
  host: 'Sarah Johnson',
  description:
    'A weekly podcast exploring the latest in technology, startups, and innovation. Join host Sarah Johnson as she interviews industry leaders and discusses the trends shaping the future of tech.',
  category: 'Technology',
  listeners: 125000,
  episodes: 156,
  rating: 4.8,
  verified: true,
  cpmRange: [25, 35],
  imageUrl: undefined,
  demographics: {
    age: { '18-24': 15, '25-34': 35, '35-44': 30, '45-54': 15, '55+': 5 },
    gender: { male: 65, female: 30, other: 5 },
    location: { 'United States': 70, 'Canada': 10, 'United Kingdom': 8, 'Other': 12 },
  },
  recentEpisodes: [
    {
      id: '1',
      title: 'The Future of AI',
      publishDate: '2025-01-10',
      duration: 3240,
      downloads: 12500,
    },
    {
      id: '2',
      title: 'Building Startups',
      publishDate: '2025-01-03',
      duration: 2880,
      downloads: 11200,
    },
  ],
  availableSlots: [
    { episodeId: '1', episodeTitle: 'The Future of AI', date: '2025-01-20', positions: ['pre-roll', 'mid-roll'] },
    { episodeId: '2', episodeTitle: 'Building Startups', date: '2025-01-27', positions: ['pre-roll', 'mid-roll', 'post-roll'] },
  ],
  growthData: [
    { date: '2024-10', listeners: 95000 },
    { date: '2024-11', listeners: 105000 },
    { date: '2024-12', listeners: 115000 },
    { date: '2025-01', listeners: 125000 },
  ],
}

export default function PodcastDetailPage({ params }: PodcastDetailPageProps) {
  const { id } = use(params)
  const podcast = mockPodcast // In real app, fetch by id

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          {/* Back Button */}
          <Link
            href="/marketplace"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Back to Marketplace
          </Link>

          {/* Hero Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-6">
            <div className="flex flex-col md:flex-row md:items-start md:space-x-6">
              <div className="w-32 h-32 bg-gradient-to-br from-blue-400 to-purple-500 rounded-lg flex items-center justify-center text-white font-bold text-4xl mb-4 md:mb-0">
                {podcast.title.charAt(0)}
              </div>
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h1 className="text-3xl font-bold text-gray-900">{podcast.title}</h1>
                  {podcast.verified && (
                    <CheckBadgeIcon className="w-6 h-6 text-blue-600" aria-label="Verified" />
                  )}
                </div>
                <p className="text-gray-600 mb-4">{podcast.description}</p>
                <div className="flex flex-wrap items-center gap-4 mb-4">
                  <div className="flex items-center space-x-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <StarIconSolid
                        key={star}
                        className={`w-5 h-5 ${
                          star <= Math.floor(podcast.rating)
                            ? 'text-yellow-400'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                    <span className="text-sm text-gray-600 ml-1">{podcast.rating}</span>
                  </div>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                    {podcast.category}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-6 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <UserGroupIcon className="w-4 h-4" />
                    <span className="font-semibold text-gray-900">
                      {(podcast.listeners / 1000).toFixed(0)}K listeners
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <ChartBarIcon className="w-4 h-4" />
                    <span>{podcast.episodes} episodes</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <TagIcon className="w-4 h-4" />
                    <span className="font-semibold text-blue-600">
                      ${podcast.cpmRange[0]}-${podcast.cpmRange[1]} CPM
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-4 md:mt-0">
                <Link
                  href={`/sponsor/booking/${podcast.id}`}
                  className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
                >
                  Book Sponsorship
                </Link>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-sm text-gray-600 mb-1">Monthly Listeners</div>
              <div className="text-2xl font-bold text-gray-900">
                {(podcast.listeners / 1000).toFixed(0)}K
              </div>
              <div className="text-sm text-green-600 mt-2">+8.7% growth</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-sm text-gray-600 mb-1">Total Episodes</div>
              <div className="text-2xl font-bold text-gray-900">{podcast.episodes}</div>
              <div className="text-sm text-blue-600 mt-2">Weekly releases</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-sm text-gray-600 mb-1">CPM Range</div>
              <div className="text-2xl font-bold text-gray-900">
                ${podcast.cpmRange[0]}-${podcast.cpmRange[1]}
              </div>
              <div className="text-sm text-purple-600 mt-2">Market rate</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-sm text-gray-600 mb-1">Rating</div>
              <div className="text-2xl font-bold text-gray-900">{podcast.rating}</div>
              <div className="text-sm text-yellow-600 mt-2">Top rated</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Growth Chart */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Listener Growth</h2>
                <div className="overflow-x-auto">
                  <div className="min-w-[500px]">
                    <TimeSeriesChart
                      data={podcast.growthData.map((d) => ({
                        date: d.date,
                        listeners: d.listeners,
                      }))}
                      dataKeys={['listeners']}
                      height={250}
                    />
                  </div>
                </div>
              </div>

              {/* Recent Episodes */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Episodes</h2>
                <div className="space-y-4">
                  {podcast.recentEpisodes.map((episode) => (
                    <div
                      key={episode.id}
                      className="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                    >
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-1">{episode.title}</h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <div className="flex items-center space-x-1">
                            <CalendarIcon className="w-4 h-4" />
                            <span>{new Date(episode.publishDate).toLocaleDateString()}</span>
                          </div>
                          <span>{Math.floor(episode.duration / 60)} min</span>
                          <span>{episode.downloads.toLocaleString()} downloads</span>
                        </div>
                      </div>
                      <button className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700">
                        Play
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Available Ad Slots */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Ad Slots</h2>
                {podcast.availableSlots.length > 0 ? (
                  <div className="space-y-3">
                    {podcast.availableSlots.map((slot, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                      >
                        <div>
                          <div className="font-medium text-gray-900">{slot.episodeTitle}</div>
                          <div className="text-sm text-gray-600 mt-1">
                            {new Date(slot.date).toLocaleDateString()} •{' '}
                            {slot.positions.map((p) => p.replace('-', ' ')).join(', ')}
                          </div>
                        </div>
                        <Link
                          href={`/sponsor/booking/${podcast.id}?episode=${slot.episodeId}`}
                          className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          Book Slot
                        </Link>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No available slots at this time</p>
                )}
              </div>
            </div>

            {/* Right Column - Sidebar */}
            <div className="space-y-6">
              {/* Demographics */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Audience Demographics</h2>
                <div className="space-y-4">
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-2">Age</div>
                    <div className="space-y-1">
                      {Object.entries(podcast.demographics.age).map(([age, pct]) => (
                        <div key={age} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">{age}</span>
                          <div className="flex items-center space-x-2 flex-1 mx-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium text-gray-900 w-10 text-right">
                              {pct}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-2">Gender</div>
                    <div className="space-y-1">
                      {Object.entries(podcast.demographics.gender).map(([gender, pct]) => (
                        <div key={gender} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 capitalize">{gender}</span>
                          <span className="text-sm font-medium text-gray-900">{pct}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-2">Top Locations</div>
                    <div className="space-y-1">
                      {Object.entries(podcast.demographics.location)
                        .sort(([, a], [, b]) => b - a)
                        .slice(0, 3)
                        .map(([location, pct]) => (
                          <div key={location} className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">{location}</span>
                            <span className="text-sm font-medium text-gray-900">{pct}%</span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Podcast Player */}
              {podcast.recentEpisodes.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Listen Now</h2>
                  <PodcastPlayer
                    episode={{
                      id: podcast.recentEpisodes[0].id,
                      title: podcast.recentEpisodes[0].title,
                      audioUrl: `/api/episodes/${podcast.recentEpisodes[0].id}/audio`,
                      duration: podcast.recentEpisodes[0].duration,
                    }}
                    showEmbedCode={true}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
