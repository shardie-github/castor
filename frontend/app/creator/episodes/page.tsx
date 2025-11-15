'use client'

import { useState } from 'react'
import { Header } from '@/components/navigation/Header'
import Link from 'next/link'
import {
  MagnifyingGlassIcon,
  PlusIcon,
  PlayIcon,
  CalendarIcon,
  ChartBarIcon,
  TagIcon,
} from '@heroicons/react/24/outline'

interface Episode {
  id: string
  title: string
  number: number
  publishDate: string
  duration: number
  downloads: number
  listeners: number
  adSlots: {
    total: number
    available: number
    booked: number
  }
  status: 'published' | 'draft' | 'scheduled'
}

// Mock data - replace with API call
const mockEpisodes: Episode[] = [
  {
    id: '1',
    title: 'The Future of Podcasting',
    number: 156,
    publishDate: '2025-01-10',
    duration: 3240,
    downloads: 12500,
    listeners: 9800,
    adSlots: { total: 3, available: 1, booked: 2 },
    status: 'published',
  },
  {
    id: '2',
    title: 'Building Your Audience',
    number: 155,
    publishDate: '2025-01-03',
    duration: 2880,
    downloads: 11200,
    listeners: 8900,
    adSlots: { total: 3, available: 0, booked: 3 },
    status: 'published',
  },
  {
    id: '3',
    title: 'Monetization Strategies',
    number: 154,
    publishDate: '2024-12-27',
    duration: 3600,
    downloads: 9800,
    listeners: 7600,
    adSlots: { total: 3, available: 2, booked: 1 },
    status: 'published',
  },
]

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

function EpisodeCard({ episode }: { episode: Episode }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-sm font-medium text-gray-500">#{episode.number}</span>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                episode.status === 'published'
                  ? 'bg-green-100 text-green-800'
                  : episode.status === 'scheduled'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {episode.status}
            </span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{episode.title}</h3>
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
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-500 mb-1">Downloads</div>
          <div className="text-lg font-semibold text-gray-900">
            {episode.downloads.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Listeners</div>
          <div className="text-lg font-semibold text-gray-900">
            {episode.listeners.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Ad Slots</div>
          <div className="text-lg font-semibold text-gray-900">
            {episode.adSlots.booked}/{episode.adSlots.total}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Available</div>
          <div
            className={`text-lg font-semibold ${
              episode.adSlots.available > 0 ? 'text-green-600' : 'text-gray-400'
            }`}
          >
            {episode.adSlots.available}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <Link
          href={`/creator/episodes/${episode.id}`}
          className="text-blue-600 hover:text-blue-700 font-medium text-sm"
        >
          View Details →
        </Link>
        <div className="flex items-center space-x-2">
          <button
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            aria-label="Edit episode"
          >
            Edit
          </button>
          <Link
            href={`/creator/episodes/${episode.id}/metrics`}
            className="px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors flex items-center space-x-1"
            aria-label="View metrics"
          >
            <ChartBarIcon className="w-4 h-4" />
            <span>Metrics</span>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function EpisodesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const filteredEpisodes = mockEpisodes.filter((episode) => {
    const matchesSearch =
      episode.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      episode.number.toString().includes(searchQuery)
    const matchesStatus = !statusFilter || episode.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Episodes</h1>
              <p className="text-gray-600 mt-2">Manage your podcast episodes and ad slots</p>
            </div>
            <Link
              href="/creator/episodes/new"
              className="mt-4 sm:mt-0 inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
            >
              <PlusIcon className="w-5 h-5 mr-2" />
              New Episode
            </Link>
          </div>

          {/* Filters */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search episodes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  aria-label="Search episodes"
                />
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setStatusFilter(null)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    statusFilter === null
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setStatusFilter('published')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    statusFilter === 'published'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Published
                </button>
                <button
                  onClick={() => setStatusFilter('draft')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    statusFilter === 'draft'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Drafts
                </button>
                <button
                  onClick={() => setStatusFilter('scheduled')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    statusFilter === 'scheduled'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Scheduled
                </button>
              </div>
            </div>
          </div>

          {/* Stats Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Total Episodes</div>
              <div className="text-2xl font-bold text-gray-900">{mockEpisodes.length}</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Total Downloads</div>
              <div className="text-2xl font-bold text-gray-900">
                {mockEpisodes.reduce((sum, e) => sum + e.downloads, 0).toLocaleString()}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Available Ad Slots</div>
              <div className="text-2xl font-bold text-green-600">
                {mockEpisodes.reduce((sum, e) => sum + e.adSlots.available, 0)}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="text-sm text-gray-600 mb-1">Booked Ad Slots</div>
              <div className="text-2xl font-bold text-blue-600">
                {mockEpisodes.reduce((sum, e) => sum + e.adSlots.booked, 0)}
              </div>
            </div>
          </div>

          {/* Episodes List */}
          {filteredEpisodes.length > 0 ? (
            <div className="space-y-4">
              {filteredEpisodes.map((episode) => (
                <EpisodeCard key={episode.id} episode={episode} />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <TagIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No episodes found</h3>
              <p className="text-gray-600 mb-6">
                {searchQuery || statusFilter
                  ? 'Try adjusting your search or filter criteria'
                  : 'Get started by creating your first episode'}
              </p>
              {!searchQuery && !statusFilter && (
                <Link
                  href="/creator/episodes/new"
                  className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <PlusIcon className="w-5 h-5 mr-2" />
                  Create First Episode
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
