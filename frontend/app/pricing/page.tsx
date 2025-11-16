'use client'

import { useState } from 'react'
import { Header } from '@/components/navigation/Header'
import { Button } from '@/components/ui/Button'
import { ConversionTracker } from '@/components/cro/ConversionTracker'
import { ABTest } from '@/components/cro/ABTest'
import { CheckIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly')

  const plans = [
    {
      name: 'Free',
      price: { monthly: 0, annual: 0 },
      description: 'Perfect for getting started',
      features: [
        'Up to 3 campaigns',
        'Basic analytics',
        '1 podcast',
        'Community support',
        'Email support',
      ],
      cta: 'Get Started',
      ctaLink: '/auth/register',
      popular: false,
    },
    {
      name: 'Professional',
      price: { monthly: 99, annual: 990 },
      description: 'For growing podcast businesses',
      features: [
        'Unlimited campaigns',
        'Advanced analytics',
        'Unlimited podcasts',
        'Priority email support',
        'API access',
        'Webhooks',
        'White-label reports',
        'Custom integrations',
      ],
      cta: 'Start Free Trial',
      ctaLink: '/settings/subscription',
      popular: true,
    },
    {
      name: 'Enterprise',
      price: { monthly: 299, annual: 2990 },
      description: 'For agencies and large teams',
      features: [
        'Everything in Professional',
        'Team collaboration',
        'Dedicated account manager',
        'Custom SLA',
        'On-premise deployment',
        'Advanced security',
        'Custom integrations',
        'Training & onboarding',
      ],
      cta: 'Contact Sales',
      ctaLink: '/contact',
      popular: false,
    },
  ]

  const getPrice = (plan: typeof plans[0]) => {
    const price = billingCycle === 'annual' ? plan.price.annual : plan.price.monthly
    if (price === 0) return 'Free'
    return `$${price}${billingCycle === 'annual' ? '/year' : '/month'}`
  }

  const getMonthlyEquivalent = (plan: typeof plans[0]) => {
    if (plan.price.monthly === 0) return null
    if (billingCycle === 'annual') {
      return `$${Math.round(plan.price.annual / 12)}/month billed annually`
    }
    return null
  }

  return (
    <>
      <ConversionTracker eventName="pricing_page_view" />
      <Header />
      <div className="min-h-screen bg-white">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-50 via-white to-purple-50 pt-20 pb-12">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">Simple, Transparent Pricing</h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
              Choose the plan that's right for you. All plans include a 14-day free trial.
            </p>

            {/* Billing Toggle */}
            <div className="flex items-center justify-center space-x-4 mb-8">
              <span className={`text-sm ${billingCycle === 'monthly' ? 'font-semibold text-gray-900' : 'text-gray-600'}`}>
                Monthly
              </span>
              <button
                onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'annual' : 'monthly')}
                className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    billingCycle === 'annual' ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className={`text-sm ${billingCycle === 'annual' ? 'font-semibold text-gray-900' : 'text-gray-600'}`}>
                Annual
                <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                  Save 17%
                </span>
              </span>
            </div>
          </div>
        </section>

        {/* Pricing Cards */}
        <section className="py-12">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-3 gap-8">
              {plans.map((plan, index) => (
                <ABTest
                  key={plan.name}
                  testName={`pricing_card_${plan.name}`}
                  variantA={
                    <div
                      className={`relative rounded-2xl border-2 p-8 ${
                        plan.popular
                          ? 'border-blue-500 shadow-xl scale-105'
                          : 'border-gray-200 shadow-sm'
                      }`}
                    >
                      {plan.popular && (
                        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                          <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                            Most Popular
                          </span>
                        </div>
                      )}
                      <div className="text-center mb-6">
                        <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                        <p className="text-gray-600 text-sm mb-4">{plan.description}</p>
                        <div className="mb-2">
                          <span className="text-4xl font-bold text-gray-900">{getPrice(plan)}</span>
                        </div>
                        {getMonthlyEquivalent(plan) && (
                          <p className="text-sm text-gray-500">{getMonthlyEquivalent(plan)}</p>
                        )}
                      </div>
                      <ul className="space-y-3 mb-8">
                        {plan.features.map((feature, featureIndex) => (
                          <li key={featureIndex} className="flex items-start">
                            <CheckIcon className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-gray-700">{feature}</span>
                          </li>
                        ))}
                      </ul>
                      <Link href={plan.ctaLink} className="block">
                        <Button
                          className="w-full"
                          variant={plan.popular ? 'primary' : 'secondary'}
                          size="lg"
                        >
                          {plan.cta}
                        </Button>
                      </Link>
                    </div>
                  }
                  variantB={
                    <div
                      className={`relative rounded-2xl border-2 p-8 bg-gradient-to-br ${
                        plan.popular
                          ? 'from-blue-50 to-purple-50 border-blue-500 shadow-xl scale-105'
                          : 'from-white to-gray-50 border-gray-200 shadow-sm'
                      }`}
                    >
                      {plan.popular && (
                        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                          <span className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                            Most Popular
                          </span>
                        </div>
                      )}
                      <div className="text-center mb-6">
                        <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                        <p className="text-gray-600 text-sm mb-4">{plan.description}</p>
                        <div className="mb-2">
                          <span className="text-4xl font-bold text-gray-900">{getPrice(plan)}</span>
                        </div>
                        {getMonthlyEquivalent(plan) && (
                          <p className="text-sm text-gray-500">{getMonthlyEquivalent(plan)}</p>
                        )}
                      </div>
                      <ul className="space-y-3 mb-8">
                        {plan.features.map((feature, featureIndex) => (
                          <li key={featureIndex} className="flex items-start">
                            <CheckIcon className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-gray-700">{feature}</span>
                          </li>
                        ))}
                      </ul>
                      <Link href={plan.ctaLink} className="block">
                        <Button
                          className="w-full"
                          variant={plan.popular ? 'primary' : 'secondary'}
                          size="lg"
                        >
                          {plan.cta}
                        </Button>
                      </Link>
                    </div>
                  }
                />
              ))}
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-20 bg-gray-50">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Frequently Asked Questions</h2>
            <div className="space-y-8">
              {[
                {
                  q: 'Can I change plans later?',
                  a: 'Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.',
                },
                {
                  q: 'What payment methods do you accept?',
                  a: 'We accept all major credit cards, PayPal, and wire transfers for Enterprise plans.',
                },
                {
                  q: 'Is there a free trial?',
                  a: 'Yes, all paid plans include a 14-day free trial. No credit card required.',
                },
                {
                  q: 'What happens if I exceed my plan limits?',
                  a: 'We\'ll notify you before you reach your limits. You can upgrade your plan or purchase additional capacity.',
                },
              ].map((faq, index) => (
                <div key={index} className="bg-white rounded-lg p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{faq.q}</h3>
                  <p className="text-gray-600">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-gradient-to-r from-blue-600 to-purple-600">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-4xl font-bold text-white mb-4">Ready to Get Started?</h2>
            <p className="text-xl text-blue-100 mb-8">
              Join thousands of podcasters and sponsors using our platform
            </p>
            <Link href="/auth/register">
              <Button size="lg" variant="secondary">
                Start Free Trial
              </Button>
            </Link>
          </div>
        </section>
      </div>
    </>
  )
}
