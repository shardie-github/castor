import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Podcast Analytics Platform | Track ROI & Attribution | Podcast Analytics',
  description: 'Enterprise-grade podcast analytics platform. Track listener behavior, measure campaign ROI, and prove attribution to sponsors. Get started free.',
  keywords: 'podcast analytics, podcast metrics, podcast ROI, podcast attribution, podcast sponsorship, podcast advertising',
  openGraph: {
    title: 'Podcast Analytics Platform | Track ROI & Attribution',
    description: 'Enterprise-grade podcast analytics platform. Track listener behavior, measure campaign ROI, and prove attribution to sponsors.',
    type: 'website',
    url: 'https://podcastanalytics.com/podcast-analytics',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Podcast Analytics Platform | Track ROI & Attribution',
    description: 'Enterprise-grade podcast analytics platform. Track listener behavior, measure campaign ROI, and prove attribution to sponsors.',
  },
}

export default function PodcastAnalyticsPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 to-purple-700 text-white py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-5xl font-bold mb-6">
              Podcast Analytics That Actually Prove ROI
            </h1>
            <p className="text-xl mb-8 text-blue-100">
              Track listener behavior, measure campaign performance, and prove attribution to sponsors with enterprise-grade analytics.
            </p>
            <div className="flex gap-4 justify-center">
              <Link
                href="/auth/register"
                className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition"
              >
                Start Free Trial
              </Link>
              <Link
                href="/demo"
                className="bg-transparent border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition"
              >
                Watch Demo
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12">
              Everything You Need to Track Podcast Performance
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">Real-Time Analytics</h3>
                <p className="text-gray-600">
                  Track listener behavior, episode performance, and audience demographics in real-time. See which episodes drive engagement and how your audience grows.
                </p>
              </div>
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">Attribution Tracking</h3>
                <p className="text-gray-600">
                  Prove ROI with multiple attribution models. Connect podcast listens to website visits, purchases, and conversions with cross-platform tracking.
                </p>
              </div>
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">Campaign Management</h3>
                <p className="text-gray-600">
                  Automate the entire campaign lifecycle. From insertion orders to performance reports, manage everything in one place.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-6">
              Ready to Prove Your Podcast ROI?
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Join thousands of podcasters who trust Podcast Analytics to track performance and prove value to sponsors.
            </p>
            <Link
              href="/auth/register"
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition inline-block"
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </section>

      {/* JSON-LD Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'SoftwareApplication',
            name: 'Podcast Analytics Platform',
            applicationCategory: 'BusinessApplication',
            operatingSystem: 'Web',
            offers: {
              '@type': 'Offer',
              price: '0',
              priceCurrency: 'USD',
            },
            aggregateRating: {
              '@type': 'AggregateRating',
              ratingValue: '4.8',
              ratingCount: '150',
            },
          }),
        }}
      />
    </div>
  )
}
