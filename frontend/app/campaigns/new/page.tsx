'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { FormField } from '@/components/forms/FormField'
import { Card } from '@/components/ui/Card'
import { LoadingState } from '@/components/ui/LoadingState'

interface Podcast {
  podcast_id: string
  title: string
}

interface Sponsor {
  sponsor_id: string
  name: string
}

export default function NewCampaignPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingData, setIsLoadingData] = useState(true)
  const [error, setError] = useState('')
  const [podcasts, setPodcasts] = useState<Podcast[]>([])
  const [sponsors, setSponsors] = useState<Sponsor[]>([])
  const [formData, setFormData] = useState({
    podcast_id: '',
    sponsor_id: '',
    name: '',
    start_date: '',
    end_date: '',
    campaign_value: '',
    attribution_method: 'promo_code',
    promo_code: '',
    notes: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        router.push('/auth/login')
        return
      }

      // Load podcasts
      // TODO: Implement podcasts API endpoint
      // For now, use placeholder
      setPodcasts([])

      // Load sponsors
      // TODO: Implement sponsors API endpoint
      // For now, use placeholder
      setSponsors([])
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
    } finally {
      setIsLoadingData(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/campaigns`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          podcast_id: formData.podcast_id,
          sponsor_id: formData.sponsor_id,
          name: formData.name,
          start_date: new Date(formData.start_date).toISOString(),
          end_date: new Date(formData.end_date).toISOString(),
          campaign_value: parseFloat(formData.campaign_value),
          attribution_method: formData.attribution_method,
          promo_code: formData.promo_code || undefined,
          notes: formData.notes || undefined,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create campaign')
      }

      // Redirect to campaign detail page
      router.push(`/campaigns/${data.campaign_id}`)
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoadingData) {
    return <LoadingState message="Loading..." />
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Create New Campaign</h1>

      <form onSubmit={handleSubmit}>
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}

        <Card className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Campaign Details</h2>
          <div className="space-y-4">
            <FormField
              label="Campaign Name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              placeholder="Q4 2024 Sponsor Campaign"
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Podcast <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.podcast_id}
                onChange={(e) => setFormData({ ...formData, podcast_id: e.target.value })}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select a podcast</option>
                {podcasts.map((podcast) => (
                  <option key={podcast.podcast_id} value={podcast.podcast_id}>
                    {podcast.title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sponsor <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.sponsor_id}
                onChange={(e) => setFormData({ ...formData, sponsor_id: e.target.value })}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select a sponsor</option>
                {sponsors.map((sponsor) => (
                  <option key={sponsor.sponsor_id} value={sponsor.sponsor_id}>
                    {sponsor.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <FormField
                label="Start Date"
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                required
              />
              <FormField
                label="End Date"
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                required
              />
            </div>

            <FormField
              label="Campaign Value ($)"
              type="number"
              step="0.01"
              value={formData.campaign_value}
              onChange={(e) => setFormData({ ...formData, campaign_value: e.target.value })}
              required
              placeholder="0.00"
            />
          </div>
        </Card>

        <Card className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Attribution</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Attribution Method
              </label>
              <select
                value={formData.attribution_method}
                onChange={(e) => setFormData({ ...formData, attribution_method: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="promo_code">Promo Code</option>
                <option value="pixel">Pixel</option>
                <option value="utm">UTM Parameters</option>
                <option value="custom">Custom</option>
              </select>
            </div>

            {formData.attribution_method === 'promo_code' && (
              <FormField
                label="Promo Code"
                type="text"
                value={formData.promo_code}
                onChange={(e) => setFormData({ ...formData, promo_code: e.target.value })}
                placeholder="PODCAST2024"
              />
            )}
          </div>
        </Card>

        <Card className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Additional Information</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Additional notes about this campaign..."
            />
          </div>
        </Card>

        <div className="flex items-center justify-between">
          <Button
            type="button"
            variant="ghost"
            onClick={() => router.back()}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isLoading}
            disabled={isLoading}
          >
            Create Campaign
          </Button>
        </div>
      </form>
    </div>
  )
}
