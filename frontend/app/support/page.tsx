'use client'

import { useState } from 'react'
import { Header } from '@/components/navigation/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { UpgradePrompt } from '@/components/cta/UpgradePrompt'
import {
  QuestionMarkCircleIcon,
  ChatBubbleLeftRightIcon,
  EnvelopeIcon,
  BookOpenIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'

export default function SupportPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const faqs = [
    {
      question: 'How do I track ROI for my campaigns?',
      answer: 'You can track ROI by setting up attribution methods like promo codes or pixels, then viewing your campaign analytics dashboard.',
    },
    {
      question: 'Can I integrate with my website?',
      answer: 'Yes! We support integrations with Shopify, Wix, WordPress, and custom websites via our API.',
    },
    {
      question: 'How do I upgrade my plan?',
      answer: 'Go to Settings > Subscription and click "Upgrade" on the plan you want. Changes take effect immediately.',
    },
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit cards and PayPal. Enterprise customers can also pay via wire transfer.',
    },
  ]

  const supportOptions = [
    {
      icon: BookOpenIcon,
      title: 'Documentation',
      description: 'Browse our comprehensive documentation',
      link: '/docs',
      available: true,
    },
    {
      icon: ChatBubbleLeftRightIcon,
      title: 'Live Chat',
      description: 'Chat with our support team (Professional+)',
      link: '/support/chat',
      available: false,
    },
    {
      icon: EnvelopeIcon,
      title: 'Email Support',
      description: 'Send us an email and we\'ll get back to you',
      link: '/support/contact',
      available: true,
    },
    {
      icon: SparklesIcon,
      title: 'Priority Support',
      description: 'Get dedicated support (Enterprise)',
      link: '/support/priority',
      available: false,
    },
  ]

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-50 via-white to-purple-50 pt-20 pb-12">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
            <QuestionMarkCircleIcon className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Support Center</h1>
            <p className="text-xl text-gray-600 mb-8">
              We're here to help. Find answers or get in touch with our team.
            </p>
          </div>
        </section>

        {/* Support Options */}
        <section className="py-12">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              {supportOptions.map((option, index) => {
                const Icon = option.icon
                return (
                  <Card
                    key={index}
                    className={`p-6 text-center ${option.available ? 'hover:shadow-lg transition-shadow cursor-pointer' : 'opacity-60'}`}
                  >
                    <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <Icon className="h-6 w-6 text-blue-600" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-2">{option.title}</h3>
                    <p className="text-sm text-gray-600 mb-4">{option.description}</p>
                    {option.available ? (
                      <Button variant="secondary" size="sm" href={option.link}>
                        Access
                      </Button>
                    ) : (
                      <UpgradePrompt
                        title="Upgrade Required"
                        description={`${option.title} is available for Professional+ plans`}
                        ctaText="Upgrade"
                        ctaLink="/settings/subscription"
                        variant="inline"
                      />
                    )}
                  </Card>
                )
              })}
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-12 bg-white">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">Frequently Asked Questions</h2>
            <div className="space-y-4">
              {faqs.map((faq, index) => (
                <Card key={index} className="p-6">
                  <h3 className="font-semibold text-gray-900 mb-2">{faq.question}</h3>
                  <p className="text-gray-600">{faq.answer}</p>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Upgrade Prompt */}
        <section className="py-12">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            <UpgradePrompt
              title="Need Priority Support?"
              description="Upgrade to Professional or Enterprise for faster response times and dedicated support."
              ctaText="Upgrade Now"
              ctaLink="/settings/subscription"
              features={['Priority email support', 'Live chat (Professional+)', 'Dedicated account manager (Enterprise)']}
              variant="card"
            />
          </div>
        </section>
      </div>
    </>
  )
}
