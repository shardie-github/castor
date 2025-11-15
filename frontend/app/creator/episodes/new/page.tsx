'use client'

import { useState } from 'react'
import { Header } from '@/components/navigation/Header'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  ArrowLeftIcon,
  CalendarIcon,
  ClockIcon,
  TagIcon,
} from '@heroicons/react/24/outline'

export default function NewEpisodePage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    publishDate: '',
    publishTime: '',
    duration: '',
    category: '',
    tags: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // In real app, submit to API
    router.push('/creator/episodes')
  }

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-8">
          <Link
            href="/creator/episodes"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Back to Episodes
          </Link>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-6">Create New Episode</h1>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Episode Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="title"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter episode title"
                  aria-required="true"
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={6}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Describe your episode..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="publishDate" className="block text-sm font-medium text-gray-700 mb-2">
                    <CalendarIcon className="w-4 h-4 inline mr-1" />
                    Publish Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    id="publishDate"
                    required
                    value={formData.publishDate}
                    onChange={(e) => setFormData({ ...formData, publishDate: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    aria-required="true"
                  />
                </div>

                <div>
                  <label htmlFor="publishTime" className="block text-sm font-medium text-gray-700 mb-2">
                    <ClockIcon className="w-4 h-4 inline mr-1" />
                    Publish Time
                  </label>
                  <input
                    type="time"
                    id="publishTime"
                    value={formData.publishTime}
                    onChange={(e) => setFormData({ ...formData, publishTime: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="duration" className="block text-sm font-medium text-gray-700 mb-2">
                    Duration (minutes)
                  </label>
                  <input
                    type="number"
                    id="duration"
                    value={formData.duration}
                    onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="60"
                  />
                </div>

                <div>
                  <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                    <TagIcon className="w-4 h-4 inline mr-1" />
                    Category
                  </label>
                  <select
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select category</option>
                    <option value="technology">Technology</option>
                    <option value="business">Business</option>
                    <option value="health">Health</option>
                    <option value="entertainment">Entertainment</option>
                    <option value="education">Education</option>
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  id="tags"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="tech, startup, innovation"
                />
              </div>

              <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200">
                <Link
                  href="/creator/episodes"
                  className="px-6 py-2 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </Link>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
                >
                  Create Episode
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  )
}
