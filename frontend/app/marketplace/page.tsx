'use client'

import { useState } from 'react'
import { Header } from '@/components/navigation/Header'
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  StarIcon,
  ChartBarIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'

interface Podcast {
  id: string
  title: string
  host: string
  category: string
  listeners: number
  episodes: number
  cpmRange: [number, number]
  rating: number
  verified: boolean
  imageUrl?: string
}

// Mock data - replace with API call
const mockPodcasts: Podcast[] = [
  {
    id: '1',
    title: 'Tech Talk Weekly',
    host: 'Sarah Johnson',
    category: 'Technology',
    listeners: 125000,
    episodes: 156,
    cpmRange: [25, 35],
    rating: 4.8,
    verified: true,
  },
  {
    id: '2',
    title: 'Business Insights',
    host: 'Michael Chen',
    category: 'Business',
    listeners: 89000,
    episodes: 203,
    cpmRange: [30, 45],
    rating: 4.9,
    verified: true,
  },
  {
    id: '3',
    title: 'Health & Wellness',
    host: 'Dr. Emily Rodriguez',
    category: 'Health',
    listeners: 67000,
    episodes: 98,
    cpmRange: [20, 30],
    rating: 4.6,
    verified: false,
  },
]

function PodcastCard({ podcast }: { podcast: Podcast }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-xl font-semibold text-gray-900">{podcast.title}</h3>
            {podcast.verified && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                Verified
              </span>
            )}
          </div>
          <p className="text-gray-600 text-sm mb-3">Hosted by {podcast.host}</p>
          <div className="flex items-center space-x-1 mb-3">
            {[1, 2, 3, 4, 5].map((star) => (
              <StarIconSolid
                key={star}
                className={`w-4 h-4 ${
                  star <= Math.floor(podcast.rating)
                    ? 'text-yellow-400'
                    : 'text-gray-300'
                }`}
              />
            ))}
            <span className="text-sm text-gray-600 ml-1">{podcast.rating}</span>
          </div>
        </div>
        <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-purple-500 rounded-lg flex items-center justify-center text-white font-bold text-xl">
          {podcast.title.charAt(0)}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-500 mb-1">Listeners</div>
          <div className="flex items-center space-x-1">
            <UserGroupIcon className="w-4 h-4 text-gray-400" />
            <span className="font-semibold text-gray-900">
              {(podcast.listeners / 1000).toFixed(0)}K
            </span>
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Episodes</div>
          <div className="flex items-center space-x-1">
            <ChartBarIcon className="w-4 h-4 text-gray-400" />
            <span className="font-semibold text-gray-900">{podcast.episodes}</span>
          </div>
        </div>
      </div>

      <div className="mb-4">
        <div className="text-xs text-gray-500 mb-1">CPM Range</div>
        <div className="text-lg font-bold text-blue-600">
          ${podcast.cpmRange[0]} - ${podcast.cpmRange[1]}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          {podcast.category}
        </span>
        <button className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors">
          View Details
        </button>
      </div>
    </div>
  )
}

export default function MarketplacePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)

  const categories = ['Technology', 'Business', 'Health', 'Entertainment', 'Education', 'Sports']

  const filteredPodcasts = mockPodcasts.filter((podcast) => {
    const matchesSearch =
      podcast.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      podcast.host.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = !selectedCategory || podcast.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          {/* Hero Section */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Podcast Marketplace</h1>
            <p className="text-gray-600">
              Discover podcast sponsorship opportunities and connect with creators
            </p>
          </div>

          {/* Search and Filters */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search podcasts or hosts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Category Filter */}
              <div className="flex items-center space-x-2 overflow-x-auto pb-2 md:pb-0">
                <button
                  onClick={() => setSelectedCategory(null)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                    selectedCategory === null
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All
                </button>
                {categories.map((category) => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                      selectedCategory === category
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>

              {/* Advanced Filters Button */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center space-x-2 whitespace-nowrap"
              >
                <FunnelIcon className="w-5 h-5" />
                <span>Filters</span>
              </button>
            </div>

            {/* Advanced Filters Panel */}
            {showFilters && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Listeners
                    </label>
                    <input
                      type="number"
                      placeholder="0"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max CPM
                    </label>
                    <input
                      type="number"
                      placeholder="100"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Verified Only
                    </label>
                    <input
                      type="checkbox"
                      className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results Count */}
          <div className="mb-4">
            <p className="text-gray-600">
              Showing <span className="font-semibold text-gray-900">{filteredPodcasts.length}</span>{' '}
              podcasts
            </p>
          </div>

          {/* Podcast Grid */}
          {filteredPodcasts.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredPodcasts.map((podcast) => (
                <PodcastCard key={podcast.id} podcast={podcast} />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <MagnifyingGlassIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No podcasts found</h3>
              <p className="text-gray-600">
                Try adjusting your search or filter criteria
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
