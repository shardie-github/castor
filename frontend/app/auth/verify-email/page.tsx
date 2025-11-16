'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'

export default function VerifyEmailPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const token = searchParams.get('token')
    const email = searchParams.get('email')

    if (!token) {
      setStatus('error')
      setMessage('Verification token is missing')
      return
    }

    // Verify email
    verifyEmail(token)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const verifyEmail = async (token: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/verify-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Verification failed')
      }

      setStatus('success')
      setMessage('Email verified successfully! You can now sign in.')
    } catch (err: any) {
      setStatus('error')
      setMessage(err.message || 'Email verification failed. The token may be invalid or expired.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          {status === 'verifying' && (
            <>
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">Verifying your email</h2>
              <p className="mt-2 text-sm text-gray-600">Please wait...</p>
            </>
          )}
          {status === 'success' && (
            <>
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">Email Verified!</h2>
              <p className="mt-2 text-sm text-gray-600">{message}</p>
              <div className="mt-6">
                <Button variant="primary" onClick={() => router.push('/auth/login')}>
                  Sign In
                </Button>
              </div>
            </>
          )}
          {status === 'error' && (
            <>
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <XCircleIcon className="h-8 w-8 text-red-600" />
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">Verification Failed</h2>
              <p className="mt-2 text-sm text-gray-600">{message}</p>
              <div className="mt-6 space-y-3">
                <Button variant="primary" onClick={() => router.push('/auth/login')}>
                  Go to Sign In
                </Button>
                <div className="text-sm">
                  <Link href="/auth/reset-password" className="font-medium text-blue-600 hover:text-blue-500">
                    Request new verification email
                  </Link>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
