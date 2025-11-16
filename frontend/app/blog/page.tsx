'use client'

import { Header } from '@/components/navigation/Header'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ConversionTracker } from '@/components/cro/ConversionTracker'
import Link from 'next/link'
import { CalendarIcon, ArrowRightIcon } from '@heroicons/react/24/outline'

export default function BlogPage() {
  const posts = [
    {
      title: 'How to Track ROI for Podcast Sponsorships',
      excerpt: 'Learn the best practices for tracking return on investment for your podcast sponsorship campaigns.',
      date: '2024-01-15',
      category: 'Analytics',
      readTime: '5 min read',
      image: '/blog/roi-tracking.jpg',
    },
    {
      title: '10 Ways to Grow Your Podcast Audience',
      excerpt: 'Discover proven strategies to increase your listener base and engagement.',
      date: '2024-01-10',
      category: 'Growth',
      readTime: '8 min read',
      image: '/blog/audience-growth.jpg',
    },
    {
      title: 'Understanding Attribution Models',
      excerpt: 'A comprehensive guide to different attribution models and when to use them.',
      date: '2024-01-05',
      category: 'Education',
      readTime: '6 min read',
      image: '/blog/attribution.jpg',
    },
  ]

  return (
    <>
      <ConversionTracker eventName="blog_page_view" />
      <Header />
      <div className="min-h-screen bg-white">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-50 via-white to-purple-50 pt-20 pb-12">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">Blog</h1>
            <p className="text-xl text-gray-600">
              Insights, tips, and best practices for podcast growth and sponsorship success
            </p>
          </div>
        </section>

        {/* Blog Posts */}
        <section className="py-12">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-3 gap-8">
              {posts.map((post, index) => (
                <Card key={index} className="overflow-hidden hover:shadow-lg transition-shadow">
                  <div className="h-48 bg-gradient-to-br from-blue-400 to-purple-500"></div>
                  <div className="p-6">
                    <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                        {post.category}
                      </span>
                      <div className="flex items-center space-x-1">
                        <CalendarIcon className="h-4 w-4" />
                        <span>{new Date(post.date).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">{post.title}</h2>
                    <p className="text-gray-600 text-sm mb-4">{post.excerpt}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">{post.readTime}</span>
                      <Link
                        href={`/blog/${post.title.toLowerCase().replace(/\s+/g, '-')}`}
                        className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium text-sm"
                      >
                        Read more
                        <ArrowRightIcon className="h-4 w-4 ml-1" />
                      </Link>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Newsletter CTA */}
        <section className="py-12 bg-gray-50">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            <Card className="p-8 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
              <div className="text-center">
                <h2 className="text-3xl font-bold mb-4">Stay Updated</h2>
                <p className="text-blue-100 mb-6">
                  Get the latest tips, insights, and updates delivered to your inbox
                </p>
                <div className="flex max-w-md mx-auto space-x-3">
                  <input
                    type="email"
                    placeholder="Enter your email"
                    className="flex-1 px-4 py-3 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-white"
                  />
                  <Button variant="secondary">Subscribe</Button>
                </div>
              </div>
            </Card>
          </div>
        </section>
      </div>
    </>
  )
}
