'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface Invoice {
  invoice_id: string
  amount: number
  currency: string
  status: string
  created_at: string
  due_date?: string
  pdf_url?: string
}

interface PaymentMethod {
  id: string
  type: string
  card?: {
    brand: string
    last4: string
    exp_month: number
    exp_year: number
  }
}

export default function BillingPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadBillingData()
  }, [])

  const loadBillingData = async () => {
    setIsLoading(true)
    setError('')

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('Not authenticated')
      }

      // Load invoices
      const invoicesResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/billing/invoices`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (invoicesResponse.ok) {
        const invoicesData = await invoicesResponse.json()
        setInvoices(invoicesData)
      }

      // Load payment methods
      const pmResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/billing/payment-methods`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (pmResponse.ok) {
        const pmData = await pmResponse.json()
        setPaymentMethods(pmData)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load billing data')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeletePaymentMethod = async (paymentMethodId: string) => {
    if (!confirm('Are you sure you want to delete this payment method?')) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/billing/payment-methods/${paymentMethodId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      )

      if (response.ok) {
        loadBillingData()
      } else {
        const data = await response.json()
        alert(data.detail || 'Failed to delete payment method')
      }
    } catch (err: any) {
      alert(err.message || 'Failed to delete payment method')
    }
  }

  if (isLoading) {
    return <LoadingState message="Loading billing information..." />
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Billing & Payment</h1>

      {/* Payment Methods */}
      <Card className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Payment Methods</h2>
          <Button variant="secondary" size="sm">
            Add Payment Method
          </Button>
        </div>

        {paymentMethods.length === 0 ? (
          <EmptyState
            title="No payment methods"
            description="Add a payment method to manage your subscription"
          />
        ) : (
          <div className="space-y-3">
            {paymentMethods.map((pm) => (
              <div
                key={pm.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  {pm.card && (
                    <>
                      <div className="w-12 h-8 bg-gray-100 rounded flex items-center justify-center">
                        <span className="text-xs font-semibold">{pm.card.brand.toUpperCase()}</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          •••• •••• •••• {pm.card.last4}
                        </p>
                        <p className="text-sm text-gray-500">
                          Expires {pm.card.exp_month}/{pm.card.exp_year}
                        </p>
                      </div>
                    </>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeletePaymentMethod(pm.id)}
                >
                  <XMarkIcon className="w-5 h-5" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Invoices */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Invoice History</h2>

        {invoices.length === 0 ? (
          <EmptyState
            title="No invoices"
            description="Your invoices will appear here once you have an active subscription"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invoices.map((invoice) => (
                  <tr key={invoice.invoice_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(invoice.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${invoice.amount.toFixed(2)} {invoice.currency.toUpperCase()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          invoice.status === 'paid'
                            ? 'bg-green-100 text-green-800'
                            : invoice.status === 'open'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {invoice.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {invoice.pdf_url && (
                        <a
                          href={invoice.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Download PDF
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
