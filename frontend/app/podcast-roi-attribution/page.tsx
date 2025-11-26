import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Podcast ROI Attribution | Prove Campaign Performance | Podcast Analytics',
  description: 'Prove podcast campaign ROI with accurate attribution tracking. Multiple attribution models, cross-platform tracking, and real-time reporting. Start tracking today.',
  keywords: 'podcast ROI, podcast attribution, campaign attribution, podcast conversion tracking, podcast analytics',
  openGraph: {
    title: 'Podcast ROI Attribution | Prove Campaign Performance',
    description: 'Prove podcast campaign ROI with accurate attribution tracking. Multiple attribution models and cross-platform tracking.',
    type: 'website',
  },
}

export default function PodcastROIAttributionPage() {
  return (
    <div className="min-h-screen bg-white">
      <section className="bg-gradient-to-br from-green-600 to-teal-700 text-white py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-5xl font-bold mb-6">
              Prove Podcast Campaign ROI with Accurate Attribution
            </h1>
            <p className="text-xl mb-8 text-green-100">
              Track conversions, measure campaign performance, and prove ROI to sponsors with multiple attribution models and cross-platform tracking.
            </p>
            <Link
              href="/auth/register"
              className="bg-white text-green-600 px-8 py-3 rounded-lg font-semibold hover:bg-green-50 transition inline-block"
            >
              Start Tracking ROI
            </Link>
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12">
              Attribution Models That Actually Work
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">First-Touch Attribution</h3>
                <p className="text-gray-600">
                  Credit the first interaction that brought a listener to your podcast. Perfect for understanding top-of-funnel impact.
                </p>
              </div>
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">Last-Touch Attribution</h3>
                <p className="text-gray-600">
                  Credit the final interaction before conversion. Ideal for measuring direct campaign impact.
                </p>
              </div>
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">Multi-Touch Attribution</h3>
                <p className="text-gray-600">
                  Distribute credit across all touchpoints. Linear, time-decay, and position-based models available.
                </p>
              </div>
              <div className="p-6 border rounded-lg">
                <h3 className="text-2xl font-semibold mb-4">Cross-Platform Tracking</h3>
                <p className="text-gray-600">
                  Connect podcast listens to website visits, purchases, and conversions across all platforms.
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
              Start Proving ROI Today
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Get accurate attribution tracking set up in minutes. No technical expertise required.
            </p>
            <Link
              href="/auth/register"
              className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 transition inline-block"
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
