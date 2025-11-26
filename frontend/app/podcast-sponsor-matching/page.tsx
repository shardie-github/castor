import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Podcast Sponsor Matching | AI-Powered Sponsor Discovery | Podcast Analytics',
  description: 'Find perfect sponsors for your podcast with AI-powered matching. Automated sponsor discovery, intelligent recommendations, and seamless campaign management.',
  keywords: 'podcast sponsors, sponsor matching, podcast advertising, sponsor discovery, podcast monetization',
  openGraph: {
    title: 'Podcast Sponsor Matching | AI-Powered Sponsor Discovery',
    description: 'Find perfect sponsors for your podcast with AI-powered matching. Automated sponsor discovery and intelligent recommendations.',
    type: 'website',
  },
}

export default function PodcastSponsorMatchingPage() {
  return (
    <div className="min-h-screen bg-white">
      <section className="bg-gradient-to-br from-purple-600 to-pink-700 text-white py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-5xl font-bold mb-6">
              Find Perfect Sponsors with AI-Powered Matching
            </h1>
            <p className="text-xl mb-8 text-purple-100">
              Stop cold-emailing sponsors. Our AI analyzes advertiser needs against your podcast content and audience to surface perfect-fit opportunities automatically.
            </p>
            <Link
              href="/auth/register"
              className="bg-white text-purple-600 px-8 py-3 rounded-lg font-semibold hover:bg-purple-50 transition inline-block"
            >
              Start Matching Sponsors
            </Link>
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12">
              How AI-Powered Matching Works
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">1. Analyze Your Podcast</h3>
                <p className="text-gray-600">
                  Our AI analyzes your podcast content, audience demographics, and performance data to understand your unique value proposition.
                </p>
              </div>
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">2. Match with Sponsors</h3>
                <p className="text-gray-600">
                  Intelligent algorithms match your podcast with sponsors looking for your exact audience and content style.
                </p>
              </div>
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">3. Manage Campaigns</h3>
                <p className="text-gray-600">
                  Seamlessly manage campaigns from matching to reporting, all in one platform.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-6">
              Start Finding Perfect Sponsors Today
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Join podcasters who use AI-powered matching to find sponsors faster and close more deals.
            </p>
            <Link
              href="/auth/register"
              className="bg-purple-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-purple-700 transition inline-block"
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
